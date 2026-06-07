# jellyfin
需要安装好jellyfin服务后做备份
```bash
sudo rsync -avh ~/dotfiles/backups/jellyfin/ /var/lib/jellyfin/data/backups/
# 这个写法只考虑文件夹下只有文件的情况，but so so
sudo chmod 644 /var/lib/jellyfin/data/backups/*
```
