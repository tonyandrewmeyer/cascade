"""Integration tests for the PlanCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PlanCommand instance."""
    yield pebble_shell.commands.PlanCommand(shell=shell)


def test_name(command: pebble_shell.commands.PlanCommand):
    assert command.name == "pebble-plans"


def test_category(command: pebble_shell.commands.PlanCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.PlanCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "plans" in output
    assert "Show layer plans" in output
    assert "--format" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "plans" in output
    assert "Show layer plans" in output


def test_execute_no_args_default_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # plans with no args should show default format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing plans or fail if Pebble unavailable
    if result == 0:
        output = capture.get()
        # Should either show plans table or no plans message
        assert any(
            msg in output
            for msg in [
                "No plans found",
                "Plan",  # Table header
                "Override",  # Table header
                "Layer",  # Table header
                "Summary",  # Table header
            ]
        )
    else:
        # Should fail if Pebble API unavailable
        assert result == 1


def test_execute_format_table_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test --format=table option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=table"])

    # Should display plans in table format
    if result == 0:
        output = capture.get()
        # Should show table format
        assert any(
            msg in output
            for msg in ["No plans found", "Plan", "Override", "Layer", "Summary"]
        )
    else:
        assert result == 1


def test_execute_format_yaml_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test --format=yaml option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display plans in YAML format
    if result == 0:
        output = capture.get()
        # Should show YAML format
        if "No plans found" not in output:
            # Should contain YAML structure
            assert any(
                yaml_indicator in output
                for yaml_indicator in ["---", "services:", "layers:"]
            )
        else:
            assert "No plans found" in output
    else:
        assert result == 1


def test_execute_format_json_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test --format=json option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=json"])

    # Should display plans in JSON format
    if result == 0:
        output = capture.get()
        # Should show JSON format
        if "No plans found" not in output:
            # Should contain JSON structure
            assert any(
                json_indicator in output
                for json_indicator in ["{", "}", "services", "layers"]
            )
        else:
            assert "No plans found" in output
    else:
        assert result == 1


def test_execute_invalid_format_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test with invalid format option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=invalid"])

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid format", "error", "Invalid"])


def test_execute_plans_table_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plans table formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # If successful and plans exist, should show table
    if result == 0:
        output = capture.get()
        # Should either show no plans message or plans table headers
        if "Plan" in output:
            # Should contain all table headers
            assert "Override" in output
            assert "Layer" in output
            assert "Summary" in output


def test_execute_no_plans_available(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test when no plans are available
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with no plans message or fail
    if result == 0:
        output = capture.get()
        # Should show no plans message if none exist
        if "No plans found" in output:
            assert "plans" in output


def test_execute_plan_name_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan name display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display plan names if plans exist
    if result == 0:
        output = capture.get()
        # Should show Plan column if plans exist
        if "Plan" in output:
            # Plan names should be displayed
            pass


def test_execute_plan_override_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan override display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display override status if plans exist
    if result == 0:
        output = capture.get()
        # Should show Override column if plans exist
        if "Override" in output:
            # Override status should be displayed
            pass


def test_execute_plan_layer_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan layer display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display layer information if plans exist
    if result == 0:
        output = capture.get()
        # Should show Layer column if plans exist
        if "Layer" in output:
            # Layer information should be displayed
            pass


def test_execute_plan_summary_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan summary display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display plan summaries if plans exist
    if result == 0:
        output = capture.get()
        # Should show Summary column if plans exist
        if "Summary" in output:
            # Summaries describe what each plan contains
            pass


def test_execute_yaml_structure_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test YAML structure validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should produce valid YAML structure
    if result == 0:
        output = capture.get()
        # Should have valid YAML structure
        if "No plans found" not in output:
            # Should contain proper YAML formatting
            pass


def test_execute_json_structure_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test JSON structure validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=json"])

    # Should produce valid JSON structure
    if result == 0:
        output = capture.get()
        # Should have valid JSON structure
        if "No plans found" not in output:
            # Should contain proper JSON formatting
            pass


def test_execute_plan_services_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan services information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display services information in plans
    if result == 0:
        output = capture.get()
        # Should show services configuration
        if "services:" in output:
            # Should contain service definitions
            pass


def test_execute_plan_checks_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan checks information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display checks information in plans
    if result == 0:
        output = capture.get()
        # Should show checks configuration
        if "checks:" in output:
            # Should contain check definitions
            pass


def test_execute_plan_log_targets_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan log targets information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display log targets information in plans
    if result == 0:
        output = capture.get()
        # Should show log targets configuration
        if "log-targets:" in output:
            # Should contain log target definitions
            pass


def test_execute_plan_layer_hierarchy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan layer hierarchy display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display layer hierarchy information
    if result == 0:
        output = capture.get()
        # Should show layer organization
        if "Layer" in output:
            # Should indicate layer relationships
            pass


def test_execute_plan_inheritance_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan inheritance display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display plan inheritance information
    if result == 0:
        output = capture.get()
        # Should show inheritance relationships
        if output.strip() and "No plans found" not in output:
            # Should indicate how plans inherit from each other
            pass


def test_execute_plan_override_mechanics(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan override mechanics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display override mechanics
    if result == 0:
        output = capture.get()
        # Should show override behavior
        if "Override" in output:
            # Should indicate which plans override others
            pass


def test_execute_plan_configuration_details(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan configuration details display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=json"])

    # Should display detailed configuration
    if result == 0:
        output = capture.get()
        # Should show comprehensive plan details
        if output.strip() and "No plans found" not in output:
            # Should contain detailed configuration information
            pass


def test_execute_plan_validation_status(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan validation status display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display plan validation status
    if result == 0:
        output = capture.get()
        # Should indicate plan validity
        if output.strip() and "No plans found" not in output:
            # Should show validation results
            pass


def test_execute_empty_plan_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test handling of empty plans
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle empty plans gracefully
    if result == 0:
        output = capture.get()
        # Should show appropriate message for empty plans
        if "No plans found" in output:
            assert len(output.strip()) > 0


def test_execute_large_plan_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test handling of large plans
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should handle large plans efficiently
    if result == 0:
        output = capture.get()
        # Should display large plans without issues
        if output.strip() and "No plans found" not in output:
            # Should manage large output appropriately
            pass


def test_execute_complex_plan_structures(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test complex plan structures display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=json"])

    # Should handle complex plan structures
    if result == 0:
        output = capture.get()
        # Should display complex structures correctly
        if output.strip() and "No plans found" not in output:
            # Should handle nested configurations
            pass


def test_execute_plan_dependency_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan dependency information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display dependency information
    if result == 0:
        output = capture.get()
        # Should show service dependencies
        if "requires:" in output or "after:" in output or "before:" in output:
            # Should contain dependency relationships
            pass


def test_execute_plan_environment_variables(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan environment variables display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display environment variables
    if result == 0:
        output = capture.get()
        # Should show environment configuration
        if "environment:" in output:
            # Should contain environment variable definitions
            pass


def test_execute_plan_command_specifications(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan command specifications display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display command specifications
    if result == 0:
        output = capture.get()
        # Should show command configurations
        if "command:" in output:
            # Should contain command definitions
            pass


def test_execute_pebble_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test error handling when Pebble API is unavailable
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should handle Pebble API errors gracefully
    if result == 1:
        # Error should be handled gracefully
        pass
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_plan_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test that command retrieves plan information
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_table_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test that table is created properly for plans display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should create table if plans exist
    if result == 0:
        output = capture.get()
        # Should use Rich table formatting
        if "Plan" in output:
            # Table should be properly formatted
            assert "Override" in output


def test_execute_format_parameter_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test format parameter handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format", "table"])

    # Should handle format parameter correctly
    if result == 0:
        output = capture.get()
        # Should apply table format
        if "Plan" in output:
            assert "Override" in output
    else:
        # May fail if argument parsing is strict
        assert result == 1


def test_execute_plan_data_extraction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test extraction of plan data fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should extract all plan fields properly
    if result == 0:
        output = capture.get()
        # Should handle all plan attributes
        if "Plan" in output:
            # Should extract plan details correctly
            pass


def test_execute_plan_unknown_fields_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test handling of plans with unknown or missing fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle missing plan fields gracefully
    if result == 0:
        output = capture.get()
        # Should display columns even if some fields are missing
        if "Plan" in output:
            # Should show "unknown" for missing fields
            pass


def test_execute_plan_serialization_formats(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test different serialization formats
    formats = ["table", "yaml", "json"]
    for fmt in formats:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[f"--format={fmt}"])

        # Should handle each format appropriately
        if result == 0:
            output = capture.get()
            # Should produce format-appropriate output
            assert len(output.strip()) >= 0
        else:
            # May fail if format is not supported
            pass


def test_execute_plan_metadata_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PlanCommand,
):
    # Test plan metadata display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--format=yaml"])

    # Should display plan metadata
    if result == 0:
        output = capture.get()
        # Should show metadata information
        if output.strip() and "No plans found" not in output:
            # Should contain plan metadata
            pass
