--- @sync entry
--- @sync peek

-- Directory preview with two modes:
--   flat (default): delegate to Yazi's built-in `folder` previewer
--   tree:           `tree -L <depth>` with colors, scrollable via J/K
--
-- Toggle with `plugin folder-tree` (bound to `T` in keymap.toml).
--
-- Adapted from Yazi's preset folder previewer (MIT) for the flat fallback.

local M = {
	tree = true,

	-- Number of levels below the hovered directory.
	depth = 2,
	-- Hard cap on captured `tree` output, keeps huge directories responsive.
	max_lines = 5000,
	-- Do not re-run `tree` on every scroll event.
	cache_ttl = 2.0,
}

local function is_local(path)
	return path:sub(1, 1) == "/" or path:match("^%a:[/\\]") ~= nil
end

local function build_tree_cmd(path)
	local cmd = {
		"tree",
		"-L",
		tostring(M.depth),
		"--dirsfirst",
		"--noreport",
		"-C",
		"--filelimit",
		"200",
	}
	if rt.mgr.show_hidden then
		cmd[#cmd + 1] = "-a"
	end

	cmd[#cmd + 1] = "--"
	cmd[#cmd + 1] = ya.quote(path)

	return table.concat(cmd, " ") .. " 2>&1 | head -n " .. tostring(M.max_lines)
end

local function read_tree(path)
	local handle = io.popen(build_tree_cmd(path), "r")
	if not handle then
		return nil
	end

	local out = handle:read("*a") or ""
	handle:close()

	-- `tree` missing or the directory cannot be read: let the flat preview
	-- handle it (it will show Yazi's own error/empty state).
	local lower = out:lower()
	if lower:find("command not found", 1, true) or lower:find("no such file or directory", 1, true) then
		return nil
	end

	local lines = {}
	for line in (out .. "\n"):gmatch("(.-)\r?\n") do
		lines[#lines + 1] = line
	end

	return #lines > 1 and lines or nil
end

function M:tree_lines(job)
	local path = tostring(job.file.url)
	local key = path .. "|" .. tostring(rt.mgr.show_hidden)
	local now = ya.time()

	local cache = self._cache
	if cache and cache.key == key and now - cache.at < M.cache_ttl then
		return cache.lines
	end

	local lines = read_tree(path)
	if not lines then
		return nil
	end

	self._cache = { key = key, at = now, lines = lines }
	return lines
end

function M:peek_tree(job)
	local path = tostring(job.file.url)
	if not is_local(path) then
		self._tree_peek = false
		return self:peek_flat(job)
	end

	local lines = self:tree_lines(job)
	if not lines then
		self._tree_peek = false
		return self:peek_flat(job)
	end

	local count = #lines
	self._tree_count = count
	self._skip = job.skip

	local bound = math.max(0, count - job.area.h)
	if job.skip > bound then
		return ya.emit("peek", { bound, only_if = job.file.url, upper_bound = true, tab = job.tab })
	end

	local first = math.min(job.skip + 1, count + 1)
	local last = math.min(first + job.area.h - 1, count)

	local visible = {}
	for i = first, last do
		visible[#visible + 1] = lines[i]
	end

	self._tree_peek = true
	return ya.preview_widget(job, ui.Text.parse(table.concat(visible, "\n")):area(job.area))
end

function M:peek_flat(job)
	if self._folder == nil then
		local ok, mod = pcall(require, "folder")
		self._folder = ok and mod or false
	end

	if self._folder then
		local ok = pcall(function()
			return self._folder:peek(job)
		end)
		if ok then
			return
		end
		self._folder = false
	end

	return self:peek_flat_fallback(job)
end

-- Fallback: a close copy of Yazi's preset `folder` previewer. It is only used
-- if requiring the preset module fails on a future Yazi version.
function M:peek_flat_fallback(job)
	local folder = cx.tab.preview.folder
	if not folder then
		return ya.preview_widget(job, ui.Line("Loading..."):area(job.area):align(ui.Align.CENTER))
	elseif folder.cwd ~= job.file.url then
		return
	end

	local bound = math.max(0, #folder.files - job.area.h)
	self._flat_count = #folder.files
	self._skip = job.skip
	if job.skip > bound then
		return ya.emit("peek", { bound, only_if = job.file.url, upper_bound = true, tab = job.tab })
	end

	if #folder.files == 0 then
		local done, err = folder.stage()
		local s = not done and "Loading..." or not err and "No items" or string.format("Error: %s", err)
		return ya.preview_widget(job, ui.Text(s):area(job.area):align(ui.Align.CENTER):wrap(ui.Wrap.YES))
	end

	local left, right = {}, {}
	for _, f in ipairs(folder.window) do
		local entity = Entity:new(f)
		left[#left + 1], right[#right + 1] = entity:redraw(), Linemode:new(f):redraw()

		local max = math.max(0, job.area.w - right[#right]:width())
		left[#left]:truncate({ max = max, ellipsis = entity:ellipsis(max) })
	end

	local marker_area = job.area({ x = math.max(0, job.area.x - 1) })
	ya.preview_widget(job, {
		ui.Text(left):area(job.area),
		ui.Text(right):area(job.area):align(ui.Align.RIGHT),
		table.unpack(Marker:new(marker_area, folder):redraw()),
	})
end

function M:seek_flat(job)
	if self._folder == nil then
		local ok, mod = pcall(require, "folder")
		self._folder = ok and mod or false
	end

	if self._folder then
		local ok = pcall(function()
			return self._folder:seek(job)
		end)
		if ok then
			return
		end
		self._folder = false
	end

	local step = math.floor(job.units * job.area.h / 10)
	local bound = math.max(0, (self._flat_count or 0) - job.area.h)
	ya.emit("peek", {
		ya.clamp(0, (self._skip or 0) + step, bound),
		only_if = job.file.url,
		tab = job.tab,
	})
end

function M:peek(job)
	if not self.tree then
		self._tree_peek = false
		return self:peek_flat(job)
	end

	return self:peek_tree(job)
end

function M:seek(job)
	if self._tree_peek then
		local step = math.floor(job.units * job.area.h / 10)
		local bound = math.max(0, (self._tree_count or 0) - job.area.h)
		ya.emit("peek", {
			ya.clamp(0, (self._skip or 0) + step, bound),
			only_if = job.file.url,
			tab = job.tab,
		})
	else
		return self:seek_flat(job)
	end
end

function M:entry()
	self.tree = not self.tree
	self._cache = nil
	self._tree_count = nil

	ya.notify({
		title = "Directory preview",
		content = self.tree and "Tree mode" or "One-level mode",
		timeout = 1.5,
	})

	ya.emit("peek", { 0, force = true })
end

return M
