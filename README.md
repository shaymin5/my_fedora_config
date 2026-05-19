# Setup

```bash
git clone https://github.com/shaymin5/my_fedora_config.git ~/dotfiles
cd ~/dotfiles
bash ./bootstrap.sh
```

# 说明

- 解决网络问题，通过usb或无线方式拿到网络代理软件的安装包
```bash
sudo dnf install /path/to/package_name.rpm
```

- ssh key生成以后连接到github
```bash
cat ~/.ssh/id_ed25519.pub
# 复制结果填到gihub后建立连接
ssh -T git@github.com
```

# 提醒
- steam第一次打开会静默下载一些东西，桌面没有反应，让人以为没正常打开。建议用命令行打开，可以看到下载情况。




