Name:           ds4to360xboxdrv
Version:        5.1.1
Release:        1%{?dist}
Summary:        DualShock 4/3 and DualSense to Xbox 360 Controller Mapper

License:        MIT
URL:            https://github.com/Pakrohk/ds4to360xboxdrv
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel
BuildRequires:  rye
BuildRequires:  python3-installer
Requires:       xboxdrv
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       systemd
Requires:       python3-evdev
Requires:       python3-pyudev

%description
ds4to360xboxdrv is a tool to emulate an Xbox 360 controller on Linux using
DualShock 4, 3, or DualSense controllers. It features a modern GTK4/Libadwaita
GUI and a robust backend using xboxdrv and evdev.

%prep
%autosetup

%build
rye build --wheel --clean

%install
python3 -m installer --destdir=%{buildroot} --prefix=%{_prefix} dist/*.whl

# Fix shebangs
sed -i '1s|#!.*|#!/usr/bin/python3|' %{buildroot}%{_bindir}/ds4to360-*

# Install system files
install -Dm644 ds4-xboxdrv.service %{buildroot}%{_unitdir}/ds4-xboxdrv.service
sed -i "s|ExecStart=.*|ExecStart=%{_bindir}/ds4to360-backend|" %{buildroot}%{_unitdir}/ds4-xboxdrv.service

install -Dm644 99-ds4-xboxdrv.rules %{buildroot}%{_udevrulesdir}/99-ds4-xboxdrv.rules
install -Dm644 ds4to360-gui.desktop %{buildroot}%{_datadir}/applications/ds4to360-gui.desktop
install -Dm644 ds4to360.conf.example %{buildroot}%{_sysconfdir}/ds4to360/ds4to360.conf

%files
%license LICENSE
%{_bindir}/ds4to360-gui
%{_bindir}/ds4to360-backend
%{python3_sitelib}/ds4to360/
%{python3_sitelib}/ds4to360xboxdrv-%{version}.dist-info/
%{_unitdir}/ds4-xboxdrv.service
%{_udevrulesdir}/99-ds4-xboxdrv.rules
%{_datadir}/applications/ds4to360-gui.desktop
%dir %{_sysconfdir}/ds4to360
%config(noreplace) %{_sysconfdir}/ds4to360/ds4to360.conf

%changelog
* Thu Feb 27 2025 Pakrohk <pakrohk@gmail.com> - 5.1.1-1
- Bug-fix and hardening release
* Wed Feb 26 2025 Pakrohk <pakrohk@gmail.com> - 5.1.0-1
- Initial multi-controller release
