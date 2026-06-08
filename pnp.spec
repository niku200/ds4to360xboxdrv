Name:           pnp
Version:        5.2.0
Release:        1%{?dist}
Summary:        PNP (PS NOT PS) – PlayStation to Xbox controller emulator for Linux

License:        MIT
URL:            https://github.com/pakrohk/pnp
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  rye
BuildRequires:  python3-installer
Requires:       xboxdrv
Requires:       evsieve
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       systemd
Requires:       python3-evdev
Requires:       python3-pyudev

%description
PNP (PS NOT PS) is a tool to emulate an Xbox 360 controller on Linux using
PlayStation DualShock or DualSense controllers. It features a modern
GTK4/Libadwaita GUI and a robust backend using xboxdrv and evsieve.

%prep
%autosetup

%build
rye build --wheel --clean

%install
python3 -m installer --destdir=%{buildroot} --prefix=%{_prefix} dist/*.whl

# Fix shebangs
sed -i '1s|#!.*|#!/usr/bin/python3|' %{buildroot}%{_bindir}/pnp-*

# Install system files
install -Dm644 pnp.service %{buildroot}%{_unitdir}/pnp.service
sed -i "s|ExecStart=.*|ExecStart=%{_bindir}/pnp-backend|" %{buildroot}%{_unitdir}/pnp.service

install -Dm644 99-pnp.rules %{buildroot}%{_udevrulesdir}/99-pnp.rules
install -Dm644 pnp.desktop %{buildroot}%{_datadir}/applications/pnp.desktop
install -Dm644 pnp.conf.example %{buildroot}%{_sysconfdir}/pnp/pnp.conf

%files
%license LICENSE
%{_bindir}/pnp-gui
%{_bindir}/pnp-backend
%{python3_sitelib}/pnp/
%{python3_sitelib}/pnp-%{version}.dist-info/
%{_unitdir}/pnp.service
%{_udevrulesdir}/99-pnp.rules
%{_datadir}/applications/pnp.desktop
%dir %{_sysconfdir}/pnp
%config(noreplace) %{_sysconfdir}/pnp/pnp.conf

%changelog
* Fri Feb 28 2025 pakrohk <pakrohk@gmail.com> - 5.2.0-1
- Rebranded to PNP (PS NOT PS)
- Stabilized multi-controller support and watchdog
