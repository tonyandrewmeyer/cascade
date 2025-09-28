"""Tests for the main PebbleShell class."""

from unittest.mock import Mock

from pebble_shell.shell import PebbleShell


class TestShell:
    """Test cases for PebbleShell."""

    def test_init(self):
        """Test shell initialization."""
        mock_client = Mock()
        # Mock the file operations for getting remote user
        mock_client.pull.side_effect = [
            Mock(
                __enter__=Mock(
                    return_value=Mock(
                        read=Mock(return_value="Uid:\t1000\t1000\t1000\t1000")
                    )
                ),
                __exit__=Mock(),
            ),
            Mock(
                __enter__=Mock(
                    return_value=Mock(
                        read=Mock(
                            return_value="user:x:1000:1000:User:/home/user:/bin/bash"
                        )
                    )
                ),
                __exit__=Mock(),
            ),
        ]

        shell = PebbleShell(mock_client)
        assert shell.client == mock_client
        assert shell.commands  # Should have commands registered
        assert shell.console is not None
        assert shell.error_console is not None

    def test_init_with_root_user(self):
        """Test shell initialization with root user."""
        mock_client = Mock()
        # Mock the file operations for getting remote user
        mock_client.pull.side_effect = [
            Mock(
                __enter__=Mock(
                    return_value=Mock(read=Mock(return_value="Uid:\t0\t0\t0\t0"))
                ),
                __exit__=Mock(),
            ),
            Mock(
                __enter__=Mock(
                    return_value=Mock(
                        read=Mock(return_value="root:x:0:0:root:/root:/bin/bash")
                    )
                ),
                __exit__=Mock(),
            ),
        ]

        shell = PebbleShell(mock_client)
        assert shell.client == mock_client

    def test_setup_commands(self):
        """Test that commands are set up properly."""
        mock_client = Mock()
        # Mock the file operations for getting remote user
        mock_client.pull.side_effect = [
            Mock(
                __enter__=Mock(
                    return_value=Mock(read=Mock(return_value="Uid:\t0\t0\t0\t0"))
                ),
                __exit__=Mock(),
            ),
            Mock(
                __enter__=Mock(
                    return_value=Mock(
                        read=Mock(return_value="root:x:0:0:root:/root:/bin/bash")
                    )
                ),
                __exit__=Mock(),
            ),
        ]

        shell = PebbleShell(mock_client)
        # Check that some basic commands exist
        assert "ls" in shell.commands
        assert "cat" in shell.commands
        assert "ps" in shell.commands
        assert "df" in shell.commands
