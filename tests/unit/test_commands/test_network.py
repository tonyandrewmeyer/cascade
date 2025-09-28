"""Tests for network commands."""

from unittest.mock import MagicMock, Mock

import pytest
from rich.panel import Panel

from pebble_shell.commands.network import (
    ArpCommand,
    NetstatCommand,
    NetworkCommand,
    RouteCommand,
    SocketStatsCommand,
)


class TestNetworkCommand:
    """Test cases for NetworkCommand."""

    @pytest.fixture
    def command(self):
        """Create NetworkCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return NetworkCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()

            if path == "/proc/net/tcp":
                tcp_content = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 0100007F:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 12345 1 0000000000000000 100 0 0 10 0
   1: 0100007F:0050 0100007F:8000 01 00000000:00000000 00:00000000 00000000     0        0 12346 1 0000000000000000 100 0 0 10 0
   2: 0100007F:0051 0100007F:8001 06 00000000:00000000 00:00000000 00000000     0        0 12347 1 0000000000000000 100 0 0 10 0
"""
                mock_file.read.return_value = tcp_content
            elif path == "/proc/net/udp":
                udp_content = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode ref pointer drops
   0: 0100007F:0035 00000000:0000 07 00000000:00000000 00:00000000 00000000     0        0 12347 2 0000000000000000 0
   1: 00000000:0044 00000000:0000 07 00000000:00000000 00:00000000 00000000     0        0 12348 2 0000000000000000 0
"""
                mock_file.read.return_value = udp_content
            elif path == "/proc/net/unix":
                unix_content = """Num       RefCount Protocol Flags    Type St Inode Path
0000000000000000: 00000002 00000000 00010000 0001 01 12348 /tmp/socket1
0000000000000001: 00000003 00000000 00000000 0002 01 12349 /tmp/socket2
0000000000000002: 00000001 00000000 00010000 0001 01 12350 /tmp/socket3
"""
                mock_file.read.return_value = unix_content
            elif path == "/proc/net/dev":
                dev_content = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:    1024      10    0    0    0     0          0         0     1024      10    0    0    0     0       0          0
  eth0: 1048576    1000    0    0    0     0          0         0  2097152    2000    0    0    0     0       0          0
  eth1:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
"""
                mock_file.read.return_value = dev_content
            else:
                raise Exception("File not found")

            return mock_file

        # Create proper context manager mock
        def side_effect_func(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_pull(path)
            mock_context_manager.__exit__.return_value = None
            return mock_context_manager

        client.pull.side_effect = side_effect_func

        return client

    def test_execute_success(self, command, mock_client, capsys):
        """Test network command success."""
        result = command.execute(mock_client, [])

        # Check that the command executed successfully
        assert result == 0

        # Check that console.print was called with a Table
        command.shell.console.print.assert_called_once()
        call_args = command.shell.console.print.call_args[0][0]

        # Verify it's a Rich Table object
        assert hasattr(call_args, "add_row")
        assert hasattr(call_args, "add_column")

    def test_execute_partial_error(self, command, capsys):
        """Test network command with partial errors."""
        # Mock client that fails on some files
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()

            if path == "/proc/net/dev":
                # Provide minimal network interface data
                dev_content = """Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:    1024      10    0    0    0     0          0         0     1024      10    0    0    0     0       0          0
"""
                mock_file.read.return_value = dev_content
            else:
                raise Exception("Permission denied")

            return mock_file

        def side_effect_func(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_pull(path)
            mock_context_manager.__exit__.return_value = None
            return mock_context_manager

        client.pull.side_effect = side_effect_func

        result = command.execute(client, [])

        # Should still succeed and print a table
        assert result == 0
        command.shell.console.print.assert_called_once()

    def test_execute_complete_error(self, command, mock_client, capsys):
        """Test network command with complete error."""
        mock_client.pull.side_effect = Exception("Complete failure")

        # The NetworkCommand should let ProcReadError propagate, but other exceptions
        # should be handled gracefully and return an error code
        with pytest.raises(Exception, match="Complete failure"):
            command.execute(mock_client, [])


class TestArpCommand:
    """Test cases for ArpCommand."""

    @pytest.fixture
    def command(self):
        """Create ArpCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return ArpCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()
            if path == "/proc/net/arp":
                arp_content = """IP address       HW type     Flags       HW address            Mask     Device
10.0.0.1         0x1         0x2         aa:bb:cc:dd:ee:ff     *        eth0
192.168.1.1      0x1         0x2         11:22:33:44:55:66     *        eth1
"""
                mock_file.read.return_value = arp_content
            else:
                raise Exception("File not found")
            return mock_file

        # Create proper context manager mock
        def side_effect_func(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_pull(path)
            mock_context_manager.__exit__.return_value = None
            return mock_context_manager

        client.pull.side_effect = side_effect_func
        return client

    def test_execute_success(self, command, mock_client, capsys):
        """Test arp command success."""
        result = command.execute(mock_client, [])

        # Check that the command executed successfully
        assert result == 0

        # Check that console.print was called with a Panel containing a Table
        command.shell.console.print.assert_called_once()
        call_args = command.shell.console.print.call_args[0][0]

        # Verify it's a Rich Panel object containing a table
        assert hasattr(call_args, "title")
        assert "ARP Table" in str(call_args.title)

    def test_execute_error(self, command, mock_client, capsys):
        """Test arp command with error."""
        mock_client.pull.side_effect = Exception("Permission denied")

        # The ArpCommand should let ProcReadError propagate, so any exception
        # during the parse process should be raised
        with pytest.raises(Exception, match="Permission denied"):
            command.execute(mock_client, [])


class TestNetstatCommand:
    """Test cases for NetstatCommand."""

    @pytest.fixture
    def command(self):
        """Create NetstatCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return NetstatCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()
            if path == "/proc/net/tcp":
                tcp_content = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 0100007F:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 12345 1 0000000000000000 100 0 0 10 0
   1: 0100007F:0050 0100007F:8000 01 00000000:00000000 00:00000000 00000000     0        0 12346 1 0000000000000000 100 0 0 10 0
"""
                mock_file.read.return_value = tcp_content
            elif path == "/proc/net/udp":
                udp_content = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode ref pointer drops
   0: 0100007F:0035 00000000:0000 07 00000000:00000000 00:00000000 00000000     0        0 12347 2 0000000000000000 0
"""
                mock_file.read.return_value = udp_content
            elif path == "/proc/net/unix":
                unix_content = """Num       RefCount Protocol Flags    Type St Inode Path
0000000000000000: 00000002 00000000 00010000 0001 01 12348 /tmp/socket
0000000000000001: 00000003 00000000 00000000 0002 01 12349
"""
                mock_file.read.return_value = unix_content
            else:
                raise Exception("File not found")
            return mock_file

        # Create proper context manager mock
        def side_effect_func(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_pull(path)
            mock_context_manager.__exit__.return_value = None
            return mock_context_manager

        client.pull.side_effect = side_effect_func
        return client

    def test_execute_tcp_default(self, command, mock_client, capsys):
        """Test netstat command with default TCP."""
        result = command.execute(mock_client, [])

        # Check that the command executed successfully
        assert result == 0

        # Check that console.print was called with a Panel
        command.shell.console.print.assert_called_once()
        call_args = command.shell.console.print.call_args[0][0]

        # Verify it's a Rich Panel object
        assert hasattr(call_args, "title")
        assert "TCP Connections:" in str(call_args.title)

    def test_execute_udp(self, command, mock_client, capsys):
        """Test netstat command with UDP."""
        result = command.execute(mock_client, ["udp"])

        # Check that the command executed successfully
        assert result == 0

        # Check that console.print was called with a Panel
        command.shell.console.print.assert_called_once()
        call_args = command.shell.console.print.call_args[0][0]

        # Verify it's a Rich Panel object
        assert hasattr(call_args, "title")
        assert "UDP Connections:" in str(call_args.title)

    def test_execute_unix(self, command, mock_client, capsys):
        """Test netstat command with UNIX sockets."""
        result = command.execute(mock_client, ["unix"])

        # Check that the command executed successfully
        assert result == 0

        # Check that console.print was called with a Panel
        command.shell.console.print.assert_called_once()
        call_args = command.shell.console.print.call_args[0][0]

        # Verify it's a Rich Panel object
        assert hasattr(call_args, "title")
        assert "UNIX Domain Sockets" in str(call_args.title)

    def test_address_parsing_moved_to_proc_reader(self, command):
        """Test that address parsing functionality has been moved to proc_reader utility."""
        from pebble_shell.utils.proc_reader import parse_network_address

        # Test localhost:22 (0x0100007F:0016)
        assert parse_network_address("0100007F:0016") == "127.0.0.1:22"
        # Test any address:80 (0x00000000:0050)
        assert parse_network_address("00000000:0050") == "0.0.0.0:80"
        # Test invalid format
        assert parse_network_address("invalid") == "invalid"

    def test_tcp_state_parsing_moved_to_proc_reader(self, command):
        """Test that TCP state parsing functionality has been moved to proc_reader utility."""
        from pebble_shell.utils.proc_reader import parse_tcp_state

        assert parse_tcp_state("01") == "ESTABLISHED"
        assert parse_tcp_state("0A") == "LISTEN"
        assert parse_tcp_state("06") == "TIME_WAIT"
        assert parse_tcp_state("FF") == "UNKNOWN(FF)"


class TestRouteCommand:
    """Test cases for RouteCommand."""

    @pytest.fixture
    def command(self):
        """Create RouteCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return RouteCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()
            if path == "/proc/net/route":
                route_content = """Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
eth0	00000000	0100000A	0003	0	0	0	00000000	0	0	0
eth0	0000000A	00000000	0001	0	0	0	0000FFFF	0	0	0
"""
                mock_file.read.return_value = route_content
            else:
                raise Exception("File not found")
            return mock_file

        # Create proper context manager mock
        def side_effect_func(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_pull(path)
            mock_context_manager.__exit__.return_value = None
            return mock_context_manager

        client.pull.side_effect = side_effect_func
        return client

    def test_execute_success(self, command, mock_client):
        """Test route command success."""
        command.execute(mock_client, [])

        mock_client.pull.assert_called_once_with("/proc/net/route")
        # Verify shell.console.print was called with a Panel
        command.shell.console.print.assert_called_once()
        args, kwargs = command.shell.console.print.call_args
        assert isinstance(args[0], Panel)
        # Check the Panel's title (now themed)
        assert args[0].title == "[magenta]Kernel IP Routing Table[/magenta]"

    def test_hex_to_ip_moved_to_proc_reader(self, command):
        """Test that IP address conversion functionality has been moved to proc_reader utility."""
        from pebble_shell.utils.proc_reader import _hex_to_ip

        assert _hex_to_ip("00000000") == "0.0.0.0"  # noqa: S104 - testing IP conversion
        assert _hex_to_ip("0100007F") == "127.0.0.1"
        assert _hex_to_ip("0100000A") == "10.0.0.1"

    def test_execute_error(self, command, mock_client):
        """Test route command with error - exception should be raised."""

        def mock_pull_error(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.side_effect = Exception("File not found")
            return mock_context_manager

        mock_client.pull.side_effect = mock_pull_error

        # Expect the exception to be raised since RouteCommand doesn't catch it
        with pytest.raises(Exception, match="File not found"):
            command.execute(mock_client, [])


class TestSocketStatsCommand:
    """Test cases for SocketStatsCommand."""

    @pytest.fixture
    def command(self):
        """Create SocketStatsCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return SocketStatsCommand(mock_shell)
