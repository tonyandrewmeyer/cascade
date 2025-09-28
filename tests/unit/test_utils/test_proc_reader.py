"""Unit tests for proc_reader utility module."""

from unittest.mock import MagicMock

import ops
import pytest

from pebble_shell.utils.proc_reader import (
    ProcReadError,
    get_boot_time_from_stat,
    get_group_name_for_gid,
    get_hostname_from_proc_sys,
    get_process_tty,
    get_user_name_for_uid,
    parse_network_address,
    parse_proc_arp,
    parse_proc_cpuinfo,
    parse_proc_diskstats,
    parse_proc_limits_file,
    parse_proc_loadavg,
    parse_proc_meminfo,
    parse_proc_mounts_file,
    parse_proc_net_connections,
    parse_proc_net_dev,
    parse_proc_route,
    parse_proc_stat,
    parse_proc_table,
    parse_proc_uptime,
    parse_proc_vmstat,
    parse_tcp_state,
    read_proc_environ,
    read_proc_file,
    read_proc_status_field,
    read_proc_status_fields,
)


class TestReadProcFile:
    """Tests for read_proc_file function."""

    def test_read_proc_file_success(self):
        """Test successful reading of a /proc file."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = "test content"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_file(mock_client, "/proc/version")

        assert result == "test content"
        mock_client.pull.assert_called_once_with("/proc/version")

    def test_read_proc_file_bytes_content(self):
        """Test reading file that returns bytes."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = b"test content"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_file(mock_client, "/proc/version")

        assert result == "test content"

    def test_read_proc_file_with_unicode_errors(self):
        """Test reading file with invalid UTF-8 bytes."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = b"\xff\xfe invalid utf8"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_file(mock_client, "/proc/version")

        # Should handle unicode errors gracefully
        assert "invalid utf8" in result

    def test_read_proc_file_path_error(self):
        """Test handling of PathError."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        with pytest.raises(ProcReadError) as exc_info:
            read_proc_file(mock_client, "/proc/nonexistent")

        error: ProcReadError = exc_info.value  # type: ignore[assignment]
        assert error.path == "/proc/nonexistent"
        assert "message" in str(error)

    def test_read_proc_file_api_error(self):
        """Test handling of APIError."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.APIError(
            {"error": "not found"}, 404, "Not Found", "File not found"
        )

        with pytest.raises(ProcReadError) as exc_info:
            read_proc_file(mock_client, "/proc/nonexistent")

        error: ProcReadError = exc_info.value  # type: ignore[assignment]
        assert error.path == "/proc/nonexistent"


class TestParseProcTable:
    """Tests for parse_proc_table function."""

    def test_parse_proc_table_basic(self):
        """Test basic table parsing."""
        content = """Header line
col1 col2 col3
val1 val2 val3
val4 val5 val6"""

        result = parse_proc_table(content, skip_header_lines=1)

        expected = [
            ["col1", "col2", "col3"],
            ["val1", "val2", "val3"],
            ["val4", "val5", "val6"],
        ]
        assert result == expected

    def test_parse_proc_table_no_headers(self):
        """Test parsing without skipping headers."""
        content = """val1 val2 val3
val4 val5 val6"""

        result = parse_proc_table(content, skip_header_lines=0)

        expected = [["val1", "val2", "val3"], ["val4", "val5", "val6"]]
        assert result == expected

    def test_parse_proc_table_empty_lines(self):
        """Test parsing with empty lines."""
        content = """Header

val1 val2 val3

val4 val5 val6
"""

        result = parse_proc_table(content, skip_header_lines=1)

        expected = [["val1", "val2", "val3"], ["val4", "val5", "val6"]]
        assert result == expected

    def test_parse_proc_table_multiple_headers(self):
        """Test parsing with multiple header lines."""
        content = """Header 1
Header 2
val1 val2 val3
val4 val5 val6"""

        result = parse_proc_table(content, skip_header_lines=2)

        expected = [["val1", "val2", "val3"], ["val4", "val5", "val6"]]
        assert result == expected


class TestReadProcStatusField:
    """Tests for read_proc_status_field function."""

    def test_read_proc_status_field_success(self):
        """Test successful field extraction."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Name:	test
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_status_field(mock_client, "1234", "Uid")

        assert result == "1000"
        mock_client.pull.assert_called_once_with("/proc/1234/status")

    def test_read_proc_status_field_not_found(self):
        """Test field not found."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Name:	test
Gid:	1000	1000	1000	1000"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_status_field(mock_client, "1234", "Uid")

        assert result is None

    def test_read_proc_status_field_empty_value(self):
        """Test field with empty value."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Name:	test
Uid:
Gid:	1000	1000	1000	1000"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_status_field(mock_client, "1234", "Uid")

        assert result is None

    def test_read_proc_status_field_self_pid(self):
        """Test reading from self process."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Name:	test
Uid:	1000	1000	1000	1000"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_status_field(mock_client, "self", "Uid")

        assert result == "1000"
        mock_client.pull.assert_called_once_with("/proc/self/status")


class TestReadProcStatusFields:
    """Tests for read_proc_status_fields function."""

    def test_read_proc_status_fields_multiple(self):
        """Test reading multiple fields."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Name:	test
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_status_fields(mock_client, "1234", ["Uid", "Gid", "Name"])

        expected = {"Uid": "1000", "Gid": "1000", "Name": "test"}
        assert result == expected

    def test_read_proc_status_fields_partial(self):
        """Test reading fields where some are missing."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Name:	test
Uid:	1000	1000	1000	1000"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_status_fields(mock_client, "1234", ["Uid", "Gid", "Name"])

        expected = {"Uid": "1000", "Name": "test"}
        assert result == expected


class TestReadProcEnviron:
    """Tests for read_proc_environ function."""

    def test_read_proc_environ_success(self):
        """Test successful environment variable reading."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = (
            "PATH=/bin:/usr/bin\x00HOME=/home/user\x00USER=testuser\x00"
        )
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_environ(mock_client, "1234")

        expected = {"PATH": "/bin:/usr/bin", "HOME": "/home/user", "USER": "testuser"}
        assert result == expected

    def test_read_proc_environ_empty_values(self):
        """Test environment variables with empty values."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = "PATH=/bin\x00EMPTY=\x00NOVALUE\x00"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_environ(mock_client, "1234")

        expected = {"PATH": "/bin", "EMPTY": "", "NOVALUE": ""}
        assert result == expected

    def test_read_proc_environ_self(self):
        """Test reading environment for self process."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = "USER=testuser\x00"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = read_proc_environ(mock_client, "self")

        assert result == {"USER": "testuser"}
        mock_client.pull.assert_called_once_with("/proc/self/environ")


class TestParseNetworkAddress:
    """Tests for parse_network_address function."""

    def test_parse_network_address_localhost(self):
        """Test parsing localhost address."""
        # 127.0.0.1:80 in little-endian hex
        hex_addr = "0100007F:0050"

        result = parse_network_address(hex_addr)

        assert result == "127.0.0.1:80"

    def test_parse_network_address_any(self):
        """Test parsing any address (0.0.0.0)."""
        hex_addr = "00000000:1F90"  # 0.0.0.0:8080

        result = parse_network_address(hex_addr)

        assert result == "0.0.0.0:8080"

    def test_parse_network_address_no_colon(self):
        """Test address without colon."""
        result = parse_network_address("invalid")

        assert result == "invalid"

    def test_parse_network_address_invalid_hex(self):
        """Test invalid hex address."""
        result = parse_network_address("ZZZZZZZZ:XXXX")

        assert result == "ZZZZZZZZ:XXXX"


class TestParseTcpState:
    """Tests for parse_tcp_state function."""

    def test_parse_tcp_state_established(self):
        """Test parsing ESTABLISHED state."""
        result = parse_tcp_state("01")
        assert result == "ESTABLISHED"

    def test_parse_tcp_state_listen(self):
        """Test parsing LISTEN state."""
        result = parse_tcp_state("0A")
        assert result == "LISTEN"

    def test_parse_tcp_state_lowercase(self):
        """Test parsing lowercase hex."""
        result = parse_tcp_state("0a")
        assert result == "LISTEN"

    def test_parse_tcp_state_unknown(self):
        """Test parsing unknown state."""
        result = parse_tcp_state("FF")
        assert result == "UNKNOWN(FF)"


class TestParseProcNetDev:
    """Tests for parse_proc_net_dev function."""

    def test_parse_proc_net_dev_success(self):
        """Test successful parsing of /proc/net/dev."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:    1234       10    0    0    0     0          0         0     1234       10    0    0    0     0       0          0
  eth0:  567890     1000    1    2    0     0          0         0   789012     2000    0    1    0     0       0          0"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_net_dev(mock_client)

        expected = [
            {
                "interface": "lo",
                "rx_bytes": 1234,
                "rx_packets": 10,
                "rx_errors": 0,
                "rx_dropped": 0,
                "tx_bytes": 1234,
                "tx_packets": 10,
                "tx_errors": 0,
                "tx_dropped": 0,
            },
            {
                "interface": "eth0",
                "rx_bytes": 567890,
                "rx_packets": 1000,
                "rx_errors": 1,
                "rx_dropped": 2,
                "tx_bytes": 789012,
                "tx_packets": 2000,
                "tx_errors": 0,
                "tx_dropped": 1,
            },
        ]
        assert result == expected

    def test_parse_proc_net_dev_insufficient_stats(self):
        """Test parsing with insufficient stats columns."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Header1
Header2
    lo:    1234       10"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_net_dev(mock_client)

        assert result == []  # Should skip interfaces with insufficient data


class TestParseProcNetConnections:
    """Tests for parse_proc_net_connections function."""

    def test_parse_proc_net_connections_tcp(self):
        """Test parsing TCP connections."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 0100007F:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 12345 1 0000000000000000 100 0 0 10 0"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_net_connections(mock_client, "tcp")

        expected = [
            {
                "protocol": "TCP",
                "local_address": "127.0.0.1:80",
                "remote_address": "0.0.0.0:0",
                "state": "LISTEN",
            }
        ]
        assert result == expected

    def test_parse_proc_net_connections_udp(self):
        """Test parsing UDP connections."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode ref pointer drops
   0: 00000000:0035 00000000:0000 07 00000000:00000000 00:00000000 00000000     0        0 12345 2 0000000000000000 0"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_net_connections(mock_client, "udp")

        expected = [
            {
                "protocol": "UDP",
                "local_address": "0.0.0.0:53",
                "remote_address": "0.0.0.0:0",
            }
        ]
        assert result == expected

    def test_parse_proc_net_connections_unix(self):
        """Test parsing UNIX domain connections."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Num       RefCount Protocol Flags    Type St Inode Path
0000000000000000: 00000002 00000000 00010000 0001 01 12345 /tmp/socket
0000000000000001: 00000003 00000000 00000000 0002 01 12346"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_net_connections(mock_client, "unix")

        expected = [
            {
                "protocol": "UNIX",
                "type": "STREAM",
                "state": "CONNECTED",
                "path": "/tmp/socket",  # noqa: S108
            },
            {
                "protocol": "UNIX",
                "type": "DGRAM",
                "state": "CONNECTED",
                "path": "<unnamed>",
            },
        ]
        assert result == expected

    def test_parse_proc_net_connections_invalid_protocol(self):
        """Test parsing with invalid protocol."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="Unsupported protocol"):
            parse_proc_net_connections(mock_client, "invalid")


class TestParseProcRoute:
    """Tests for parse_proc_route function."""

    def test_parse_proc_route_success(self):
        """Test successful parsing of routing table."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
eth0	00000000	0100007F	0003	0	0	100	00000000	0	0	0
lo	0000007F	00000000	0001	0	0	0	000000FF	0	0	0"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_route(mock_client)

        expected = [
            {
                "interface": "eth0",
                "destination": "0.0.0.0",  # noqa: S104 - test data for default route
                "gateway": "127.0.0.1",
                "flags": "UG",
                "metric": "100",
                "mask": "0.0.0.0",  # noqa: S104 - test data for netmask
            },
            {
                "interface": "lo",
                "destination": "127.0.0.0",
                "gateway": "0.0.0.0",  # noqa: S104 - test data for loopback route
                "flags": "U",
                "metric": "0",
                "mask": "255.0.0.0",
            },
        ]
        assert result == expected


class TestParseProcMeminfo:
    """Tests for parse_proc_meminfo function."""

    def test_parse_proc_meminfo_success(self):
        """Test successful parsing of /proc/meminfo."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        meminfo_content = """MemTotal:       16384000 kB
MemFree:         8192000 kB
MemAvailable:   12288000 kB
Buffers:          512000 kB
Cached:          2048000 kB
SwapCached:           0 kB
Active:          4096000 kB
Inactive:        1024000 kB
SwapTotal:       2048000 kB
SwapFree:        2048000 kB
Dirty:                64 kB
Writeback:             0 kB
"""
        mock_file.read.return_value = meminfo_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_meminfo(mock_client)

        assert result["MemTotal"] == 16384000
        assert result["MemFree"] == 8192000
        assert result["MemAvailable"] == 12288000
        assert result["Buffers"] == 512000
        assert result["Cached"] == 2048000
        assert result["SwapTotal"] == 2048000
        assert result["SwapFree"] == 2048000
        assert result["Dirty"] == 64
        assert result["Writeback"] == 0

    def test_parse_proc_meminfo_missing_kb_suffix(self):
        """Test parsing /proc/meminfo without kB suffix."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        meminfo_content = """MemTotal:       16384000
MemFree:         8192000 kB
VmallocTotal:   34359738367 kB
VmallocUsed:       0
"""
        mock_file.read.return_value = meminfo_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_meminfo(mock_client)

        assert result["MemTotal"] == 16384000
        assert result["MemFree"] == 8192000
        assert result["VmallocTotal"] == 34359738367
        assert result["VmallocUsed"] == 0

    def test_parse_proc_meminfo_invalid_values(self):
        """Test parsing /proc/meminfo with some invalid values."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        meminfo_content = """MemTotal:       16384000 kB
MemFree:         invalid_value kB
MemAvailable:   12288000 kB
BadLine
NoColon 123456
EmptyValue:
"""
        mock_file.read.return_value = meminfo_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_meminfo(mock_client)

        assert result["MemTotal"] == 16384000
        assert result["MemAvailable"] == 12288000
        assert "MemFree" not in result  # Should be skipped due to invalid value
        assert len(result) == 2  # Only valid entries

    def test_parse_proc_meminfo_error(self):
        """Test error handling when reading /proc/meminfo fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_meminfo(mock_client)

        assert "/proc/meminfo" in str(exc_info.value)


class TestParseProcUptime:
    """Tests for parse_proc_uptime function."""

    def test_parse_proc_uptime_success(self):
        """Test successful parsing of /proc/uptime."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        uptime_content = "12345.67 98765.43\n"
        mock_file.read.return_value = uptime_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_uptime(mock_client)

        assert result["uptime_seconds"] == 12345.67
        assert result["idle_seconds"] == 98765.43

    def test_parse_proc_uptime_invalid_format(self):
        """Test parsing /proc/uptime with invalid format."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        uptime_content = "invalid\n"
        mock_file.read.return_value = uptime_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_uptime(mock_client)

        assert "/proc/uptime" in str(exc_info.value)

    def test_parse_proc_uptime_error(self):
        """Test error handling when reading /proc/uptime fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_uptime(mock_client)

        assert "/proc/uptime" in str(exc_info.value)


class TestParseProcLoadavg:
    """Tests for parse_proc_loadavg function."""

    def test_parse_proc_loadavg_success(self):
        """Test successful parsing of /proc/loadavg."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        loadavg_content = "0.25 0.50 0.75 2/305 12345\n"
        mock_file.read.return_value = loadavg_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_loadavg(mock_client)

        assert result["load_1min"] == "0.25"
        assert result["load_5min"] == "0.50"
        assert result["load_15min"] == "0.75"
        assert result["running_processes"] == 2
        assert result["total_processes"] == 305
        assert result["last_pid"] == 12345

    def test_parse_proc_loadavg_invalid_processes(self):
        """Test parsing /proc/loadavg with invalid process format."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        loadavg_content = "0.25 0.50 0.75 invalid 12345\n"
        mock_file.read.return_value = loadavg_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_loadavg(mock_client)

        assert result["load_1min"] == "0.25"
        assert result["load_5min"] == "0.50"
        assert result["load_15min"] == "0.75"
        assert result["running_processes"] == 0
        assert result["total_processes"] == 0
        assert result["last_pid"] == 12345

    def test_parse_proc_loadavg_insufficient_fields(self):
        """Test parsing /proc/loadavg with insufficient fields."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        loadavg_content = "0.25 0.50\n"
        mock_file.read.return_value = loadavg_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_loadavg(mock_client)

        assert "/proc/loadavg" in str(exc_info.value)

    def test_parse_proc_loadavg_error(self):
        """Test error handling when reading /proc/loadavg fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_loadavg(mock_client)

        assert "/proc/loadavg" in str(exc_info.value)


class TestParseProcArp:
    """Tests for parse_proc_arp function."""

    def test_parse_proc_arp_success(self):
        """Test successful parsing of ARP table."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """IP address       HW type     Flags       HW address            Mask     Device
192.168.1.1      0x1         0x2         aa:bb:cc:dd:ee:ff     *        eth0
192.168.1.100    0x1         0x2         11:22:33:44:55:66     *        eth0"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_arp(mock_client)

        expected = [
            {
                "ip_address": "192.168.1.1",
                "hw_type": "0x1",
                "flags": "0x2",
                "hw_address": "aa:bb:cc:dd:ee:ff",
                "mask": "*",
                "device": "eth0",
            },
            {
                "ip_address": "192.168.1.100",
                "hw_type": "0x1",
                "flags": "0x2",
                "hw_address": "11:22:33:44:55:66",
                "mask": "*",
                "device": "eth0",
            },
        ]
        assert result == expected


class TestUserGroupLookup:
    """Tests for user and group name lookup functions."""

    def test_get_user_name_for_uid_success(self):
        """Test successful user lookup."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
testuser:x:1000:1000:Test User:/home/testuser:/bin/bash"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_user_name_for_uid(mock_client, "1000")

        assert result == "testuser"

    def test_get_user_name_for_uid_not_found(self):
        """Test user lookup when UID not found."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """root:x:0:0:root:/root:/bin/bash"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_user_name_for_uid(mock_client, "1000")

        assert result is None

    def test_get_user_name_for_uid_file_error(self):
        """Test user lookup when file cannot be read."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        result = get_user_name_for_uid(mock_client, "1000")

        assert result is None

    def test_get_group_name_for_gid_success(self):
        """Test successful group lookup."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """root:x:0:
daemon:x:1:
testgroup:x:1000:testuser"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_group_name_for_gid(mock_client, "1000")

        assert result == "testgroup"

    def test_get_group_name_for_gid_not_found(self):
        """Test group lookup when GID not found."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = """root:x:0:"""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_group_name_for_gid(mock_client, "1000")

        assert result is None


class TestParseProcStat:
    """Tests for parse_proc_stat function."""

    def test_parse_proc_stat_success(self):
        """Test successful parsing of /proc/stat."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        stat_content = """cpu  123456 7890 98765 4321098 5432 0 1234 0 0 0
cpu0 61728 3945 49382 2160549 2716 0 617 0 0 0
cpu1 61728 3945 49383 2160549 2716 0 617 0 0 0
intr 12345678
ctxt 87654321
btime 1609459200
processes 123456
procs_running 2
procs_blocked 1
softirq 456789 123 456 789 0 321 654 987 0 147 258
"""
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_stat(mock_client)

        assert result["cpu"]["user"] == 123456
        assert result["cpu"]["nice"] == 7890
        assert result["cpu"]["system"] == 98765
        assert result["cpu"]["idle"] == 4321098
        assert result["cpu"]["iowait"] == 5432
        assert result["cpu"]["irq"] == 0
        assert result["cpu"]["softirq"] == 1234

        cpus_data = result["cpus"]
        assert isinstance(cpus_data, dict), (
            f"cpus should be dict, got {type(cpus_data)}"
        )
        assert "0" in cpus_data
        assert "1" in cpus_data
        assert cpus_data["0"]["user"] == 61728
        assert cpus_data["1"]["user"] == 61728

        assert result["system"]["intr"] == 12345678
        assert result["system"]["ctxt"] == 87654321
        assert result["system"]["btime"] == 1609459200
        assert result["system"]["processes"] == 123456
        assert result["system"]["procs_running"] == 2
        assert result["system"]["procs_blocked"] == 1

    def test_parse_proc_stat_minimal_format(self):
        """Test parsing /proc/stat with minimal fields."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        stat_content = """cpu  100 200 300 400
intr 12345
"""
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_stat(mock_client)

        assert result["cpu"]["user"] == 100
        assert result["cpu"]["nice"] == 200
        assert result["cpu"]["system"] == 300
        assert result["cpu"]["idle"] == 400
        assert result["cpu"]["iowait"] == 0  # Default value
        assert result["system"]["intr"] == 12345

    def test_parse_proc_stat_error(self):
        """Test error handling when reading /proc/stat fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_stat(mock_client)

        assert "/proc/stat" in str(exc_info.value)


class TestParseProcVmstat:
    """Tests for parse_proc_vmstat function."""

    def test_parse_proc_vmstat_success(self):
        """Test successful parsing of /proc/vmstat."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        vmstat_content = """nr_free_pages 123456
nr_zone_inactive_anon 78901
nr_zone_active_anon 234567
nr_zone_inactive_file 345678
nr_zone_active_file 456789
nr_zone_unevictable 0
nr_zone_write_pending 12
nr_mlock 0
nr_page_table_pages 1234
nr_kernel_stack 5678
pgpgin 123456789
pgpgout 987654321
pswpin 12345
pswpout 54321
pgalloc_dma 0
pgalloc_dma32 123456
pgalloc_normal 789012
pgfree 912345
"""
        mock_file.read.return_value = vmstat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_vmstat(mock_client)

        assert result["nr_free_pages"] == 123456
        assert result["nr_zone_inactive_anon"] == 78901
        assert result["pgpgin"] == 123456789
        assert result["pgpgout"] == 987654321
        assert result["pswpin"] == 12345
        assert result["pswpout"] == 54321
        assert result["pgfree"] == 912345

    def test_parse_proc_vmstat_invalid_values(self):
        """Test parsing /proc/vmstat with some invalid values."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        vmstat_content = """nr_free_pages 123456
invalid_line
nr_zone_active_anon invalid_value
pgpgin 987654
empty_value
"""
        mock_file.read.return_value = vmstat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_vmstat(mock_client)

        assert result["nr_free_pages"] == 123456
        assert result["pgpgin"] == 987654
        assert (
            "nr_zone_active_anon" not in result
        )  # Should be skipped due to invalid value
        assert len([k for k in result if k.startswith("nr_")]) == 1

    def test_parse_proc_vmstat_error(self):
        """Test error handling when reading /proc/vmstat fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_vmstat(mock_client)

        assert "/proc/vmstat" in str(exc_info.value)


class TestParseProcDiskstats:
    """Tests for parse_proc_diskstats function."""

    def test_parse_proc_diskstats_success(self):
        """Test successful parsing of /proc/diskstats."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        diskstats_content = """   8       0 sda 123456 7890 9876543 12345 56789 1011 4567890 23456 0 78901 98765
   8       1 sda1 98765 4321 8765432 9876 43210 987 3456789 18765 0 65432 87654
   8      16 sdb 11111 2222 3333333 4444 55555 666 7777777 8888 0 9999 10101
 259       0 nvme0n1 567890 12345 11111111 67890 123456 2345 22222222 134567 0 145678 278901
"""
        mock_file.read.return_value = diskstats_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_diskstats(mock_client)

        assert len(result) == 4

        # Test first device (sda)
        sda = result[0]
        assert sda["major"] == 8
        assert sda["minor"] == 0
        assert sda["device"] == "sda"
        assert sda["reads"] == 123456
        assert sda["read_merges"] == 7890
        assert sda["read_sectors"] == 9876543
        assert sda["read_time"] == 12345
        assert sda["writes"] == 56789
        assert sda["write_merges"] == 1011
        assert sda["write_sectors"] == 4567890
        assert sda["write_time"] == 23456
        assert sda["io_in_progress"] == 0
        assert sda["io_time"] == 78901
        assert sda["io_weighted_time"] == 98765

        # Test nvme device
        nvme = result[3]
        assert nvme["device"] == "nvme0n1"
        assert nvme["major"] == 259
        assert nvme["minor"] == 0

    def test_parse_proc_diskstats_insufficient_fields(self):
        """Test parsing /proc/diskstats with insufficient fields."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        diskstats_content = """   8       0 sda 123 456 789  # Only 6 fields, should be skipped
   8       1 sda1 98765 4321 8765432 9876 43210 987 3456789 18765 0 65432 87654  # 13 fields, valid
"""
        mock_file.read.return_value = diskstats_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_diskstats(mock_client)

        # Should only have one entry (sda1) since sda has insufficient fields
        assert len(result) == 1
        assert result[0]["device"] == "sda1"

    def test_parse_proc_diskstats_invalid_values(self):
        """Test parsing /proc/diskstats with invalid numeric values."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        diskstats_content = """   8       0 sda invalid 7890 9876543 12345 56789 1011 4567890 23456 0 78901 98765
   8       1 sda1 98765 4321 8765432 9876 43210 987 3456789 18765 0 65432 87654
"""
        mock_file.read.return_value = diskstats_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_diskstats(mock_client)

        # Should only have sda1 since sda has invalid numeric value
        assert len(result) == 1
        assert result[0]["device"] == "sda1"

    def test_parse_proc_diskstats_empty_lines(self):
        """Test parsing /proc/diskstats with empty lines."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        diskstats_content = """
   8       0 sda 123456 7890 9876543 12345 56789 1011 4567890 23456 0 78901 98765

   8       1 sda1 98765 4321 8765432 9876 43210 987 3456789 18765 0 65432 87654
"""
        mock_file.read.return_value = diskstats_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_diskstats(mock_client)

        assert len(result) == 2
        assert result[0]["device"] == "sda"
        assert result[1]["device"] == "sda1"

    def test_parse_proc_diskstats_error(self):
        """Test error handling when reading /proc/diskstats fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_diskstats(mock_client)

        assert "/proc/diskstats" in str(exc_info.value)


class TestParseProcCpuinfo:
    """Tests for parse_proc_cpuinfo function."""

    def test_parse_proc_cpuinfo_success(self):
        """Test successful parsing of /proc/cpuinfo."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        cpuinfo_content = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
stepping	: 10
microcode	: 0xf0
cpu MHz		: 2100.000
cache size	: 8192 KB
physical id	: 0
siblings	: 8
core id		: 0
cpu cores	: 4
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8
bugs		:
bogomips	: 4200.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz
stepping	: 10
microcode	: 0xf0
cpu MHz		: 2100.000
cache size	: 8192 KB
physical id	: 0
siblings	: 8
core id		: 1
cpu cores	: 4
apicid		: 2
initial apicid	: 2
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8
bugs		:
bogomips	: 4200.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:

"""
        mock_file.read.return_value = cpuinfo_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_cpuinfo(mock_client)

        assert result["cpu_count"] == 2
        cpus_data = result["cpus"]
        assert isinstance(cpus_data, list), (
            f"cpus should be list, got {type(cpus_data)}"
        )
        assert len(cpus_data) == 2

        # Test first CPU
        cpu0 = cpus_data[0]
        assert cpu0["processor"] == "0"
        assert cpu0["vendor_id"] == "GenuineIntel"
        assert cpu0["model name"] == "Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz"
        assert cpu0["cpu cores"] == "4"
        assert cpu0["cache size"] == "8192 KB"

        # Test second CPU
        cpu1 = cpus_data[1]
        assert cpu1["processor"] == "1"
        assert cpu1["core id"] == "1"
        assert cpu1["apicid"] == "2"

    def test_parse_proc_cpuinfo_single_cpu(self):
        """Test parsing /proc/cpuinfo with single CPU."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        cpuinfo_content = """processor	: 0
vendor_id	: AuthenticAMD
cpu family	: 23
model		: 49
model name	: AMD EPYC 7302P 16-Core Processor
stepping	: 0
microcode	: 0x8301038
cpu MHz		: 3000.000
cache size	: 512 KB
physical id	: 0
siblings	: 32
core id		: 0
cpu cores	: 16
apicid		: 0
"""
        mock_file.read.return_value = cpuinfo_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_cpuinfo(mock_client)

        assert result["cpu_count"] == 1
        cpus_data = result["cpus"]
        assert isinstance(cpus_data, list), (
            f"cpus should be list, got {type(cpus_data)}"
        )
        assert len(cpus_data) == 1
        assert cpus_data[0]["model name"] == "AMD EPYC 7302P 16-Core Processor"
        assert cpus_data[0]["cpu cores"] == "16"

    def test_parse_proc_cpuinfo_malformed_lines(self):
        """Test parsing /proc/cpuinfo with malformed lines."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        cpuinfo_content = """processor	: 0
vendor_id	: GenuineIntel
invalid_line_without_colon
model name	: Intel CPU
: value_without_key
processor	: 1
model name	: Intel CPU 2
"""
        mock_file.read.return_value = cpuinfo_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_cpuinfo(mock_client)

        assert result["cpu_count"] == 2
        cpus_data = result["cpus"]
        assert isinstance(cpus_data, list), (
            f"cpus should be list, got {type(cpus_data)}"
        )
        assert len(cpus_data) == 2
        assert cpus_data[0]["model name"] == "Intel CPU"
        assert cpus_data[1]["model name"] == "Intel CPU 2"

    def test_parse_proc_cpuinfo_error(self):
        """Test error handling when reading /proc/cpuinfo fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            parse_proc_cpuinfo(mock_client)

        assert "/proc/cpuinfo" in str(exc_info.value)


class TestProcReadError:
    """Tests for ProcReadError exception."""

    def test_proc_read_error_attributes(self):
        """Test ProcReadError has correct attributes."""
        error = ProcReadError("/proc/test", "test message")

        assert error.path == "/proc/test"
        assert error.message == "test message"
        assert str(error) == "Error reading /proc/test: test message"


class TestGetProcessTty:
    """Tests for get_process_tty function."""

    def test_get_process_tty_with_tty(self):
        """Test getting TTY for a process with TTY."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        # TTY field (7th) is "34816" - should convert to pts/0
        stat_content = "1234 (bash) S 1233 1234 34816 34816 1234 4194304 123 456 0 0 10 20 0 0 20 0 1 0 123456 12345678 890 18446744073709551615 4194304 4456789 140736123456 0 0 0 65536 3670016 1266777851 0 0 0 17 1 0 0 0 0 0"
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_process_tty(mock_client, "1234")

        assert result == "pts/0"
        mock_client.pull.assert_called_once_with("/proc/1234/stat")

    def test_get_process_tty_no_tty(self):
        """Test getting TTY for a process without TTY."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        # TTY field (7th) is "0" - should return "?"
        stat_content = "1234 (daemon) S 1 1234 0 0 1234 4194304 123 456 0 0 10 20 0 0 20 0 1 0 123456 12345678 890 18446744073709551615 4194304 4456789 140736123456 0 0 0 0 0 0 0 0 0 17 1 0 0 0 0 0"
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_process_tty(mock_client, "1234")

        assert result == "?"

    def test_get_process_tty_insufficient_fields(self):
        """Test getting TTY with insufficient fields in stat file."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        # Only 5 fields - should return "?"
        stat_content = "1234 (test) S 1 1234"
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_process_tty(mock_client, "1234")

        assert result == "?"

    def test_get_process_tty_read_error(self):
        """Test getting TTY when stat file read fails."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        with pytest.raises(ProcReadError) as exc_info:
            get_process_tty(mock_client, "1234")

        assert "/proc/1234/stat" in str(exc_info.value)


class TestGetBootTimeFromStat:
    """Tests for get_boot_time_from_stat function."""

    def test_get_boot_time_success(self):
        """Test successful boot time extraction."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        stat_content = """cpu  123 456 789 0 0 0 0 0 0 0
btime 1609459200
ctxt 123456
"""
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_boot_time_from_stat(mock_client)
        assert result == 1609459200

    def test_get_boot_time_no_btime(self):
        """Test when btime line is missing."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        stat_content = """cpu  123 456 789 0 0 0 0 0 0 0
ctxt 123456
"""
        mock_file.read.return_value = stat_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        with pytest.raises(ProcReadError):
            get_boot_time_from_stat(mock_client)

    def test_get_boot_time_read_error(self):
        """Test when /proc/stat cannot be read."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        with pytest.raises(ProcReadError):
            get_boot_time_from_stat(mock_client)


class TestParseProcLimitsFile:
    """Tests for parse_proc_limits_file function."""

    def test_parse_limits_success(self):
        """Test successful limits parsing."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        limits_content = """Limit                     Soft Limit           Hard Limit           Units
Max cpu time              unlimited            unlimited            seconds
Max file size             unlimited            unlimited            bytes
Max data size             unlimited            unlimited            bytes
"""
        mock_file.read.return_value = limits_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_limits_file(mock_client, "self")

        assert "Max cpu time" in result
        assert result["Max cpu time"]["soft"] == "unlimited"
        assert result["Max cpu time"]["hard"] == "unlimited"
        assert result["Max cpu time"]["units"] == "seconds"

    def test_parse_limits_empty_file(self):
        """Test parsing empty limits file."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = ""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        with pytest.raises(ProcReadError):
            parse_proc_limits_file(mock_client, "self")

    def test_parse_limits_read_error(self):
        """Test when limits file cannot be read."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        with pytest.raises(ProcReadError):
            parse_proc_limits_file(mock_client, "self")


class TestParseProcMountsFile:
    """Tests for parse_proc_mounts_file function."""

    def test_parse_mounts_success(self):
        """Test successful mounts parsing."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mounts_content = """sysfs /sys sysfs rw,nosuid,nodev,noexec,relatime 0 0
proc /proc proc rw,nosuid,nodev,noexec,relatime 0 0
/dev/sda1 / ext4 rw,relatime,errors=remount-ro 0 0
"""
        mock_file.read.return_value = mounts_content
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_mounts_file(mock_client)

        assert len(result) == 3
        assert result[0]["device"] == "sysfs"
        assert result[0]["mountpoint"] == "/sys"
        assert result[0]["fstype"] == "sysfs"
        assert result[0]["options"] == "rw,nosuid,nodev,noexec,relatime"

    def test_parse_mounts_empty_file(self):
        """Test parsing empty mounts file."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = ""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = parse_proc_mounts_file(mock_client)
        assert result == []

    def test_parse_mounts_read_error(self):
        """Test when mounts file cannot be read."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        with pytest.raises(ProcReadError):
            parse_proc_mounts_file(mock_client)


class TestGetHostnameFromProcSys:
    """Tests for get_hostname_from_proc_sys function."""

    def test_get_hostname_success(self):
        """Test successful hostname reading."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = "test-host\n"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        result = get_hostname_from_proc_sys(mock_client)
        assert result == "test-host"

    def test_get_hostname_read_error(self):
        """Test when hostname file cannot be read."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        with pytest.raises(ProcReadError):
            get_hostname_from_proc_sys(mock_client)


class TestReadProcCmdline:
    """Tests for read_proc_cmdline function."""

    def test_read_cmdline_success(self):
        """Test successful cmdline reading with null bytes."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = (
            "python3\x00/usr/bin/script.py\x00--arg1\x00--arg2\x00"
        )
        mock_client.pull.return_value.__enter__.return_value = mock_file

        from src.pebble_shell.utils.proc_reader import read_proc_cmdline

        result = read_proc_cmdline(mock_client, "1234")
        assert result == "python3 /usr/bin/script.py --arg1 --arg2"

    def test_read_cmdline_empty(self):
        """Test reading empty cmdline."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = ""
        mock_client.pull.return_value.__enter__.return_value = mock_file

        from src.pebble_shell.utils.proc_reader import read_proc_cmdline

        result = read_proc_cmdline(mock_client, "1234")
        assert result == "unknown"

    def test_read_cmdline_read_error(self):
        """Test when cmdline file cannot be read."""
        mock_client = MagicMock()
        mock_client.pull.side_effect = ops.pebble.PathError("kind", "message")

        from src.pebble_shell.utils.proc_reader import read_proc_cmdline

        result = read_proc_cmdline(mock_client, "1234")
        assert result == "unknown"

    def test_read_cmdline_self_process(self):
        """Test reading cmdline for self process."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = "python\x00-m\x00pytest\x00"
        mock_client.pull.return_value.__enter__.return_value = mock_file

        from src.pebble_shell.utils.proc_reader import read_proc_cmdline

        result = read_proc_cmdline(mock_client, "self")
        assert result == "python -m pytest"
