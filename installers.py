from pathlib import Path
from shutil import which
from subprocess import TimeoutExpired
from typing import List
from cli import car_apt_warning, comm
from exceptions import InstallationError


CURRENT_PATH = Path.cwd()
CONFIG_FILES_PATH = f"{CURRENT_PATH}/files"
DOWNLOADS_PATH = f"{CURRENT_PATH}/inst_downloads"


def list_apt_pkgs() -> List[str]:
    """Returns a list of apt packages to be installed."""

    pkgs = [
        # essential for development
        "build-essential",
        "python3-dev",
        "pkg-config",

        # needed for other software installation and/or they're simply useful
        "apt-transport-https",
        "cmake",
        "curl",
        "ca-certificates",
        "gnupg",
        "lsb-release",

        "htop",                         # better than top
        "mmv",                          # move/copy/append/link multiple files according to a set of wildcard patterns
        "neovim",
        "tmux",                         # terminal multiplexer

    ]

    return pkgs


def list_snap_pkgs() -> List[str]:
    """Returns a list of snap apps."""

    pkgs = [
        "bitwarden",
        "jdownloader2",
        "libreoffice",
        "signal-desktop",
        "spotify",
        "vlc",

        "sublime-text --classic",
        "code --classic",
    ]

    return pkgs


def pre_install() -> bool:
    """Creates "downloads" directory to be used at any point during the installation and post-installation phase."""

    cmd = f"mkdir {DOWNLOADS_PATH}"
    _, errs = comm(cmd)
    if errs:
        raise InstallationError("Failed pre-installation procedure.")
    return True


def install_apt_pkgs() -> bool:
    """Installs apt packages."""

    pkgs = list_apt_pkgs()

    print("Installing Apt packages...")

    for pkg in pkgs:
        print(f"Installing {pkg}...")
        _, errs_ = comm(f"apt install -y {pkg}")
        if errs_:
            errs = car_apt_warning(errs_)
            if errs:
                raise InstallationError(f"Failed to install {pkg}.")

    print("Apt packages successfully installed.")
    return True


def install_snap_pkgs() -> bool:
    """Installs snap pkgs."""

    pkgs_ = list_snap_pkgs()
    install_cmd = "snap install "

    # separate any package that needs the `--classic` flag
    # for now it simply assumes that if there is a flag, it will be exactly the `--classic` flag
    # fortunately, all the snap pkgs I need either don't need a flag or the flag is `--classic`. For now.

    unflg_pkgs: List[str] = []
    flg_pkgs: List[str] = []
    flag = "--classic"

    for pkg in pkgs_:
        if flag in pkg:
            flg_pkgs.append(pkg)
        else:
            unflg_pkgs.append(pkg)

    print("Installing Snap packages...")

    for pkg in flg_pkgs:
        print(f"Installing {pkg}...")
        _, errs = comm(f"{install_cmd} {pkg}")
        if errs:
            raise InstallationError(f"Failed to install {pkg}.")

    for pkg in unflg_pkgs:
        print(f"Installing {pkg}...")
        _, errs = comm(f"{install_cmd} {pkg}")
        if errs:
            raise InstallationError(f"Failed to install {pkg}.")
    
    print("Snap packages were successfully installed.")

    return True


def install_brave_browser() -> bool:
    """Installs Brave Browser.

    Installation instructions from <https://brave.com/linux/#linux>.
    """

    cmd = ("curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg "
    "https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg"
           )

    print("Getting Brave Browser's signing keys...")
    _, errs = comm(cmd)
    if errs:
        raise InstallationError("Failed to add Brave Browser's fingerprint.")
    print("Successfully added Brave Browser's signing keys.")

    cmd = ("echo "
           "\"deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64] "
           "https://brave-browser-apt-release.s3.brave.com/ stable main\""
           " | "
           "tee /etc/apt/sources.list.d/brave-browser-release.list"
          )

    print("Adding Brave Browser's apt repository...")
    _, errs = comm(cmd)
    if errs:
        raise InstallationError("Failed to add Brave Browser's ppa.")
    print("Successfully added Brave Browser's apt repository.")

    cmd = "apt update -y && apt install -y brave-browser"

    print("Installing brave-browser...")
    _, errs_ = comm(cmd)
    if errs_:
        errs = car_apt_warning(errs_)
        if errs:
            raise InstallationError("Failed to install Brave Browser's apt package.")
    print("Installation successful.")
    return True


def install_docker() -> bool:
    """Installs Docker Engine and Docker Compose v2.

    Installation instructions from <https://docs.docker.com/engine/install/ubuntu/> and
    <https://docs.docker.com/engine/install/linux-postinstall/>
    """

    cmd = ("curl -fsSL https://download.docker.com/linux/ubuntu/gpg"
           " | "
           "gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg"
          )

    print("Adding Docker signing keys...")
    _, errs = comm(cmd)
    if errs:
        raise InstallationError("Failed to add Docker's fingerprint.")
    print("Successfully added Docker's signing keys.")

    cmd = ("echo "
           "\"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] "
           "https://download.docker.com/linux/ubuntu "
           "$(lsb_release -cs) stable\""
           " | "
           "tee /etc/apt/sources.list.d/docker.list > /dev/null"
           )

    print("Adding Docker apt repository...")
    _, errs = comm(cmd)
    if errs:
        raise InstallationError("Failed to add Docker's ppa.")
    print("Docker's apt repository successfully added.")

    print("Updating apt repositories...")
    cmd = "apt update -y"
    _, errs_ = comm(cmd)
    if errs_:
        errs = car_apt_warning(errs_)
        if errs:
            raise InstallationError("Failed to install Docker apt packages.")
    print("Apt repositories successfully updated.")

    pkgs = ["docker-ce", "docker-ce-cli", "containerd.io"]
    for pkg in pkgs:
        print(f"Installing {pkg}...")
        _, errs_ = comm(f"apt install -y {pkg}")
        if errs_:
            errs = car_apt_warning(errs_)
            if errs:
                raise InstallationError(f"Failed to install Docker {pkg}.")
    print("Installation successful.")

    # post-install step required for all Linux distros

    cmd = "usermod -aG docker $USER"
    print("Adding user to docker group...")
    _, errs = comm(cmd)
    if errs:
        print(errs)
        raise InstallationError("Failed to add user to docker group.")
    print("Successfully added user to Docker group")

    return True


def install_fish_shell() -> bool:
    """Installs Fish Shell.

    Installation instructions from <https://launchpad.net/~fish-shell/+archive/ubuntu/release-3>
    """

    cmd = "apt-add-repository ppa:fish-shell/release-3 -y"
    print("Adding Fish shell's apt repository...")
    _, errs = comm(cmd)
    if errs:
        print(errs)
        raise InstallationError("Failed to add Fish's ppa.")
    print("Succesfully added.")

    cmd = "apt update -y && apt install -y fish"
    print("Installing fish...")
    _, errs_ = comm(cmd)
    if errs_:
        errs = car_apt_warning(errs_)
        if errs:
            print(errs)
            raise InstallationError("Failed to install Fish shell.")
    print("Installation successful.")

    return True


def install_google_chrome() -> bool:
    """Installs Google Chrome."""

    file_name = "google-chrome-stable_current_amd64.deb"
    file_url = f"https://dl.google.com/linux/direct/{file_name}"
    cmd = f"cd {DOWNLOADS_PATH} && curl -sO {file_url}"

    print("Downloading Google Chrome's .deb file...")
    _, errs = comm(cmd)
    if errs:
        print(errs)
        raise InstallationError("Failed to download Google Chrome's .deb file.")
    print("Download successful.")

    cmd = f"cd {DOWNLOADS_PATH} && apt install -y ./{file_name}"
    print("Installing Google Chrome from .deb file...")
    _, errs_ = comm(cmd)
    if errs_:
        errs = car_apt_warning(errs_)
        if errs:
            print(errs)
            raise InstallationError("Failed to install Google Chrome from .deb file.")
    print("Installation successful.")

    return True


def install_poetry() -> bool:
    """Installs Poetry (package manager for Python).

    Installation instructions from <https://python-poetry.org/docs/>.
    """

    python_v = ""
    if which("python3"):
        python_v = "3"
    cmd = f"curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python{python_v} -"
    print("Executing Poetry's installation script...")
    _, errs = comm(cmd)
    if errs:
        print(errs)
        InstallationError("Poetry was not installed.")
    print("Execution successful.")

    return True


def install_qbittorrent() -> bool:
    """Installs qbittorrent.
    
    Installation instructions from <https://www.qbittorrent.org/download.php>.
    """

    cmd = "add-apt-repository ppa:qbittorrent-team/qbittorrent-stable -y"
    print("Adding qbittorent's apt repository...")
    _, errs = comm(cmd)
    if errs:
        print(errs)
        raise InstallationError("Failed to add qbittorrent ppa.")
    print("Successfully added.")

    cmd = "apt update -y && apt install qbittorrent -y"
    print("Installing qbittorrent...")
    _, errs_ = comm(cmd)
    if errs_:
        errs = car_apt_warning(errs_)
        if errs:
            print(errs)
            raise InstallationError("Failed to install qbittorrent.")
    print("Installation successful.")

    return True

    
def install_not_ppkd_prog() -> bool:
    """Installs all programs not in apt nor snap packages."""

    # brave browser
    print("Installing Brave Browser...")
    try:
        install_brave_browser()
    except (InstallationError, TimeoutExpired):
        raise InstallationError("Brave browser was not installed")
    else:
        print("Successfully installed Brave Browser.")

    # docker
    print("Installing Docker...")
    try:
        install_docker()
    except (InstallationError, TimeoutExpired):
        raise InstallationError("Docker was not installed.")
    else:
        print("Successfully installed Docker.")


    # fish shell
    print("Installing Fish shell...")
    try:
        install_fish_shell()
    except (InstallationError, TimeoutExpired):
        raise InstallationError("Fish shell was not installed.")
    print("Successfully installed Fish shell.")

    # google chrome
    print("Installing Google Chrome...")
    try:
        install_google_chrome()
    except (InstallationError, TimeoutExpired):
        raise InstallationError("Google Chrome was not installed.")
    print("Successfully installed Google Chrome.")

    # poetry
    print("Installing Poetry...")
    try:
        install_poetry()
    except (InstallationError, TimeoutExpired):
        raise InstallationError("Poetry was not installed.")
    print("Successfully installed Poetry.")

    # qbittorrent
    print("Installing qbittorrent...")
    try:
        install_poetry()
    except (InstallationError, TimeoutExpired):
        raise InstallationError("qbittorrent was not installed.")
    print("Successfully installed qbittorrent.")


    return True


def cleanup() -> bool:
    """Removes Downloads directory and apt cleans and apt autocleans the system."""

    cmd = f"rm -r {DOWNLOADS_PATH}"
    _, errs = comm(cmd)
    if errs:
        return False

    cmd = "apt autoclean && apt clean"
    _, errs_ = comm(cmd)
    if errs_:
        errs = car_apt_warning(errs_)
        if errs:
            return False

    return True


# testing installation commands
#if __name__ == "__main__":
#
#    pre_install()
#    install_apt_pkgs()
#    install_snap_pkgs()
#    install_not_ppkd_prog()
#    cleanup()
