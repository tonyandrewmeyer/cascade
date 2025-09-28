"""Integration tests for proc_reader utility module.

These tests use real proc file samples to test the parsing functions
with realistic data formats.
"""

from unittest.mock import MagicMock

from pebble_shell.utils.proc_reader import (
    parse_proc_arp,
    parse_proc_net_connections,
    parse_proc_net_dev,
    parse_proc_route,
    read_proc_environ,
    read_proc_status_fields,
)


class TestProcReaderIntegration:
    """Integration tests with realistic /proc file data."""

    def create_mock_client(self, file_content: str):
        """Create a mock client that returns the given content."""
        mock_client = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = file_content
        mock_client.pull.return_value.__enter__.return_value = mock_file
        return mock_client

    def test_real_proc_net_dev_parsing(self):
        """Test parsing with real /proc/net/dev content."""
        # Real content from Ubuntu system
        content = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 2776770663 2933941    0    0    0     0          0         0 2776770663 2933941    0    0    0     0       0          0
enp0s3: 2147483647  156789    0   12    0     0          0         0 1547483647  123456    0    0    0     0       0          0
docker0:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
"""
        mock_client = self.create_mock_client(content)

        result = parse_proc_net_dev(mock_client)

        assert len(result) == 3

        # Check loopback interface
        lo_interface = result[0]
        assert lo_interface["interface"] == "lo"
        assert lo_interface["rx_bytes"] == 2776770663
        assert lo_interface["rx_packets"] == 2933941
        assert lo_interface["tx_bytes"] == 2776770663
        assert lo_interface["tx_packets"] == 2933941

        # Check ethernet interface
        eth_interface = result[1]
        assert eth_interface["interface"] == "enp0s3"
        assert eth_interface["rx_bytes"] == 2147483647
        assert eth_interface["rx_dropped"] == 12

        # Check docker interface
        docker_interface = result[2]
        assert docker_interface["interface"] == "docker0"
        assert docker_interface["rx_bytes"] == 0

    def test_real_proc_net_tcp_parsing(self):
        """Test parsing with real /proc/net/tcp content."""
        # Real TCP connection data
        content = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 00000000:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 15691 1 0000000000000000 100 0 0 10 0
   1: 0100007F:0277 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1000        0 16872 1 0000000000000000 100 0 0 10 0
   2: 0100007F:0CEA 0100007F:A696 01 00000000:00000000 00:00000000 00000000  1000        0 18234 1 0000000000000000 20 4 27 10 -1
"""
        mock_client = self.create_mock_client(content)

        result = parse_proc_net_connections(mock_client, "tcp")

        assert len(result) == 3

        # Check SSH listening port (22)
        ssh_conn = result[0]
        assert ssh_conn["protocol"] == "TCP"
        assert ssh_conn["local_address"] == "0.0.0.0:22"
        assert ssh_conn["remote_address"] == "0.0.0.0:0"
        assert ssh_conn["state"] == "LISTEN"

        # Check localhost listening
        local_conn = result[1]
        assert local_conn["local_address"] == "127.0.0.1:631"  # CUPS
        assert local_conn["state"] == "LISTEN"

        # Check established connection
        est_conn = result[2]
        assert est_conn["local_address"] == "127.0.0.1:3306"  # MySQL
        assert est_conn["state"] == "ESTABLISHED"

    def test_real_proc_net_unix_parsing(self):
        """Test parsing with real /proc/net/unix content."""
        content = """Num       RefCount Protocol Flags    Type St Inode Path
0000000000000000: 00000002 00000000 00010000 0001 01 16293 /run/systemd/private
0000000000000000: 00000002 00000000 00010000 0001 01 16294 /run/systemd/notify
0000000000000000: 00000003 00000000 00000000 0002 01 16295
0000000000000000: 00000002 00000000 00000000 0001 03 16296 @/tmp/.X11-unix/X0
"""
        mock_client = self.create_mock_client(content)

        result = parse_proc_net_connections(mock_client, "unix")

        assert len(result) == 4

        # Check systemd socket
        systemd_sock = result[0]
        assert systemd_sock["protocol"] == "UNIX"
        assert systemd_sock["type"] == "STREAM"
        assert systemd_sock["state"] == "CONNECTED"
        assert systemd_sock["path"] == "/run/systemd/private"

        # Check datagram socket
        dgram_sock = result[2]
        assert dgram_sock["type"] == "DGRAM"
        assert dgram_sock["path"] == "<unnamed>"

        # Check abstract socket
        x11_sock = result[3]
        assert x11_sock["path"] == "@/tmp/.X11-unix/X0"

    def test_real_proc_route_parsing(self):
        """Test parsing with real /proc/net/route content."""
        content = """Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
enp0s3	00000000	0101A8C0	0003	0	0	100	00000000	0	0	0
enp0s3	0001A8C0	00000000	0001	0	0	100	00FFFFFF	0	0	0
docker0	000011AC	00000000	0001	0	0	0	0000FFFF	0	0	0
"""
        mock_client = self.create_mock_client(content)

        result = parse_proc_route(mock_client)

        assert len(result) == 3

        # Check default route
        default_route = result[0]
        assert default_route["interface"] == "enp0s3"
        assert default_route["destination"] == "0.0.0.0"  # noqa: S104 - testing default route
        assert default_route["gateway"] == "192.168.1.1"
        assert "G" in default_route["flags"]  # Gateway flag
        assert "U" in default_route["flags"]  # Up flag

        # Check local network route
        local_route = result[1]
        assert local_route["destination"] == "192.168.1.0"
        assert local_route["gateway"] == "0.0.0.0"  # noqa: S104 - testing local route (no gateway)
        assert local_route["mask"] == "255.255.255.0"

        # Check docker route
        docker_route = result[2]
        assert docker_route["interface"] == "docker0"
        assert docker_route["destination"] == "172.17.0.0"

    def test_real_proc_arp_parsing(self):
        """Test parsing with real /proc/net/arp content."""
        content = """IP address       HW type     Flags       HW address            Mask     Device
192.168.1.1      0x1         0x2         52:54:00:12:34:56     *        enp0s3
192.168.1.100    0x1         0x2         08:00:27:ab:cd:ef     *        enp0s3
192.168.1.254    0x1         0x0         00:00:00:00:00:00     *        enp0s3
"""
        mock_client = self.create_mock_client(content)

        result = parse_proc_arp(mock_client)

        assert len(result) == 3

        # Check gateway entry
        gateway_entry = result[0]
        assert gateway_entry["ip_address"] == "192.168.1.1"
        assert gateway_entry["hw_type"] == "0x1"
        assert gateway_entry["flags"] == "0x2"
        assert gateway_entry["hw_address"] == "52:54:00:12:34:56"
        assert gateway_entry["device"] == "enp0s3"

        # Check incomplete entry (flags 0x0)
        incomplete_entry = result[2]
        assert incomplete_entry["ip_address"] == "192.168.1.254"
        assert incomplete_entry["flags"] == "0x0"
        assert incomplete_entry["hw_address"] == "00:00:00:00:00:00"

    def test_real_proc_status_parsing(self):
        """Test parsing with real /proc/*/status content."""
        content = """Name:	bash
Umask:	0022
State:	S (sleeping)
Tgid:	1234
Ngid:	0
Pid:	1234
PPid:	1000
TracerPid:	0
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
FDSize:	256
Groups:	4 20 24 27 30 46 118 128 1000
NStgid:	1234
NSpid:	1234
NSpgid:	1234
NSsid:	1234
VmPeak:	   21644 kB
VmSize:	   21512 kB
VmLck:	       0 kB
VmPin:	       0 kB
VmHWM:	    4932 kB
VmRSS:	    4932 kB
"""
        mock_client = self.create_mock_client(content)

        result = read_proc_status_fields(
            mock_client, "1234", ["Name", "Uid", "Gid", "State", "VmRSS"]
        )

        expected = {
            "Name": "bash",
            "Uid": "1000",
            "Gid": "1000",
            "State": "S",
            "VmRSS": "4932",
        }
        assert result == expected

    def test_real_proc_environ_parsing(self):
        """Test parsing with real /proc/*/environ content."""
        # Real environment data (null-separated)
        content = "USER=testuser\x00PATH=/usr/local/bin:/usr/bin:/bin\x00HOME=/home/testuser\x00SHELL=/bin/bash\x00TERM=xterm-256color\x00LANG=en_US.UTF-8\x00"
        mock_client = self.create_mock_client(content)

        result = read_proc_environ(mock_client, "1234")

        expected = {
            "USER": "testuser",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": "/home/testuser",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
            "LANG": "en_US.UTF-8",
        }
        assert result == expected

    def test_edge_case_malformed_proc_files(self):
        """Test handling of malformed /proc file content."""
        # Test with truncated /proc/net/dev
        malformed_netdev = """Inter-|   Receive
 face |bytes    packets errs drop fifo frame compressed multicast
    lo: 1234
    eth0: incomplete line"""

        mock_client = self.create_mock_client(malformed_netdev)
        result = parse_proc_net_dev(mock_client)

        # Should skip malformed entries
        assert len(result) == 0

    def test_performance_with_large_proc_files(self):
        """Test performance with large /proc file content."""
        # Generate large /proc/net/tcp content (1000 connections)
        header = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
        connections = []
        for i in range(1000):
            # Generate varied IP addresses and states
            local_ip = f"{(i % 256):02X}{((i // 256) % 256):02X}{((i // 65536) % 256):02X}{((i // 16777216) % 256):02X}"
            port = f"{(8000 + i % 1000):04X}"
            state = (
                "01" if i % 2 == 0 else "0A"
            )  # Alternate between ESTABLISHED and LISTEN
            line = f"   {i}: {local_ip}:{port} 00000000:0000 {state} 00000000:00000000 00:00000000 00000000  1000        0 {16000 + i} 1 0000000000000000 20 4 27 10 -1"
            connections.append(line)

        large_content = header + "\n".join(connections)
        mock_client = self.create_mock_client(large_content)

        result = parse_proc_net_connections(mock_client, "tcp")

        assert len(result) == 1000
        # Verify first and last entries
        assert result[0]["state"] == "ESTABLISHED"
        assert result[999]["state"] == "LISTEN"
        assert result[0]["protocol"] == "TCP"

    def test_unicode_handling_in_proc_files(self):
        """Test handling of unicode characters in proc files."""
        # Environment with unicode values
        unicode_content = (
            "USER=测试用户\x00PATH=/usr/bin\x00DISPLAY=:0.0\x00LANG=zh_CN.UTF-8\x00"
        )
        mock_client = self.create_mock_client(unicode_content)

        result = read_proc_environ(mock_client, "1234")

        assert result["USER"] == "测试用户"
        assert result["LANG"] == "zh_CN.UTF-8"

    def test_empty_proc_files(self):
        """Test handling of empty /proc files."""
        mock_client = self.create_mock_client("")

        # Test various parsing functions with empty content
        assert parse_proc_net_dev(mock_client) == []
        assert parse_proc_net_connections(mock_client, "tcp") == []
        assert parse_proc_route(mock_client) == []
        assert parse_proc_arp(mock_client) == []
        assert read_proc_environ(mock_client, "1234") == {}

    def test_whitespace_variations_in_proc_files(self):
        """Test handling of various whitespace patterns in proc files."""
        # /proc/net/dev with irregular spacing
        content_with_spaces = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:       1234        10    0    0    0     0          0         0      1234        10    0    0    0     0       0          0
  eth0:     567890      1000    0    0    0     0          0         0    789012      2000    0    0    0     0       0          0
"""
        mock_client = self.create_mock_client(content_with_spaces)

        result = parse_proc_net_dev(mock_client)

        assert len(result) == 2
        assert result[0]["interface"] == "lo"
        assert result[0]["rx_bytes"] == 1234
        assert result[1]["interface"] == "eth0"
        assert result[1]["rx_bytes"] == 567890
