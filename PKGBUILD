# Maintainer: pakrohk <pakrohk@gmail.com>
pkgname=pnp
pkgver=5.2.0
pkgrel=1
pkgdesc="PNP (PS NOT PS) – PlayStation to Xbox controller emulator for Linux using xboxdrv and evsieve with GTK4/Libadwaita GUI"
arch=('any')
url="https://github.com/pakrohk/pnp"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'systemd' 'xboxdrv' 'evsieve' 'polkit' 'python-evdev' 'python-pyudev')
makedepends=('rye' 'python-installer' 'python-build')
backup=('etc/pnp/pnp.conf')
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz"
        "pnp.service"
        "99-pnp.rules"
        "pnp.desktop"
        "pnp.conf.example")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

build() {
  cd "${pkgname}-${pkgver}"
  rye build --wheel --clean
}

package() {
  cd "${pkgname}-${pkgver}"

  # Install the wheel
  python -m installer --destdir="$pkgdir" --prefix=/usr dist/*.whl

  # Fix shebangs in /usr/bin scripts to use system python3
  sed -i '1s|#!.*|#!/usr/bin/python3|' "$pkgdir"/usr/bin/pnp-*

  # Install systemd service
  install -Dm644 ../pnp.service "${pkgdir}/usr/lib/systemd/system/pnp.service"
  sed -i "s|ExecStart=.*|ExecStart=/usr/bin/pnp-backend|" "${pkgdir}/usr/lib/systemd/system/pnp.service"

  # Install udev rules
  install -Dm644 ../99-pnp.rules "${pkgdir}/usr/lib/udev/rules.d/99-pnp.rules"

  # Install desktop file
  install -Dm644 ../pnp.desktop "${pkgdir}/usr/share/applications/pnp.desktop"

  # Install default config
  install -Dm644 ../pnp.conf.example "${pkgdir}/etc/pnp/pnp.conf"

  # Install license
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
