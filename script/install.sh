# 安装nvidia-container, 用于给docker提供nvidia-smi
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo |
    sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
# 版本是26年6月最新版本，可以去https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html找最新的
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.19.1-1
sudo dnf install -y \
    nvidia-container-toolkit-${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base-${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools-${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1-${NVIDIA_CONTAINER_TOOLKIT_VERSION}
