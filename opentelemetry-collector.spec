%global goipath         github.com/os-observability/redhat-opentelemetry-collector

Version:                0.102.1
ExcludeArch:            %{ix86} s390 ppc ppc64 aarch64

%gometa

%global common_description %{expand:
Collector with the supported components for a Red Hat build of OpenTelemetry}

%global golicenses    LICENSE
%global godocs        README.md

Name:           opentelemetry-collector
Release:        3%{?dist}
Summary:        Red Hat build of OpenTelemetry

License:        Apache-2.0

Source0:        %{name}-%{version}.tar.gz
Source1:        otel_collector_journald.te

BuildRequires: systemd
BuildRequires: %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}
BuildRequires: binutils
BuildRequires: git
BuildRequires:  policycoreutils, checkpolicy, selinux-policy-devel

Requires(pre): /usr/sbin/useradd, /usr/bin/getent
Requires(postun): /usr/sbin/userdel

%description
%{common_description}

%prep
mkdir -p _build
mkdir -p _build/bin

%setup -q -n redhat-%{name}-%{version}

%build

# Compile the SELinux policy module
checkmodule -M -m -o otel_collector_journald.mod %{SOURCE1}
semodule_package -o otel_collector_journald.pp -m otel_collector_journald.mod

go build -ldflags "-s -w" -v -buildmode pie -mod vendor -o %{gobuilddir}/bin/opentelemetry-collector

%define debug_package %{nil}

%install
# create expected directory layout
mkdir -p %{buildroot}%{_datadir}/selinux/packages
mkdir -p %{buildroot}%{_sysconfdir}/opentelemetry-collector
mkdir -p %{buildroot}%{_sysconfdir}/opentelemetry-collector/configs
mkdir -p %{buildroot}%{_unitdir}

# install files
install -m 0644 ./otel_collector_journald.pp %{buildroot}%{_datadir}/selinux/packages/otel_collector_journald.pp
install -p -m 0644  ./00-default-receivers.yaml %{buildroot}%{_sysconfdir}/opentelemetry-collector/configs/00-default-receivers.yaml
install -p -m 0644  ./opentelemetry-collector.service %{buildroot}%{_unitdir}/%{name}.service

install -m 0755 -vd                     %{buildroot}%{_bindir}
install -m 0755 -vp %{gobuilddir}/bin/* %{buildroot}%{_bindir}/
install -m 0755 -p ./opentelemetry-collector-with-options %{buildroot}%{_bindir}/

%pre
/usr/bin/getent group observability > /dev/null || /usr/sbin/groupadd -r observability
/usr/bin/getent passwd observability > /dev/null || /usr/sbin/useradd -r -M -s /sbin/nologin -g observability -G systemd-journal observability

%postun
/usr/sbin/userdel observability

%post
semodule -i %{_datadir}/selinux/packages/otel_collector_journald.pp
restorecon -v %{_bindir}/opentelemetry-collector
/bin/systemctl --system daemon-reload 2>&1

%preun
if [ $1 -eq 0 ]; then
    /bin/systemctl --quiet stop %{name}.service
    /bin/systemctl --quiet disable %{name}.service
    semodule -r otel_collector_journald
fi

%posttrans
/bin/systemctl is-enabled %{name}.service >/dev/null 2>&1
if [  $? -eq 0 ]; then
    /bin/systemctl restart %{name}.service >/dev/null
fi

%check
%gocheck

%files
%{_unitdir}/%{name}.service
%{_sysconfdir}/opentelemetry-collector/configs/00-default-receivers.yaml
%{_datadir}/selinux/packages/otel_collector_journald.pp

%license %{golicenses}
%doc %{godocs}
%{_bindir}/*

%changelog
* Wed Aug 01 2024 Benedikt Bongartz <bongartz@redhat.com> - 0.102.1-3
- Add default selinux policy for journald receiver
- Bump revision
* Wed Jul 24 2024 Benedikt Bongartz <bongartz@redhat.com> - 0.102.1-2
- spec: strip go binary
* Tue Jul 16 2024 Benedikt Bongartz <bongartz@redhat.com> - 0.102.1-1
- rpm: trim date (#89) (Ben B)
- Add transform processor (#88) (Ruben Vargas)
* Fri Jun 28 2024 Benedikt Bongartz <bongartz@redhat.com> - 0.102.1
- move microshift specifics into another rpm
- bump collector version to 0.102.0
* Fri Apr 12 2024 Benedikt Bongartz <bongartz@redhat.com> - 0.95.0
- add observability user that is part of the systemd-journal group
- add opentelemetry collector config folder (`/etc/opentelemetry-collector/configs`)
- add opentelemetry collector default config
- add microshift manifests
* Thu Feb 1 21:59:10 CET 2024 Nina Olear <nolear@redhat.com> - 0.93.4
- First package for Copr
