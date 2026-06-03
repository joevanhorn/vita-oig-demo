# ==============================================================================
# OPC INFRASTRUCTURE OUTPUTS
# ==============================================================================

output "opc_agents" {
  description = "OPC agent details"
  value = {
    for k, v in module.opc_agents : k => {
      instance_id   = v.instance_id
      private_ip    = v.private_ip
      public_ip     = v.public_ip
      instance_name = v.instance_name
      ssm_command   = v.ssm_session_command
    }
  }
}

output "security_group_id" {
  description = "Shared security group ID"
  value       = aws_security_group.opc_shared.id
}

output "ssm_commands" {
  description = "SSM session commands for each agent"
  value = {
    for k, v in module.opc_agents : k => v.ssm_session_command
  }
}

output "connection_summary" {
  description = "Summary of deployed OPC agents"
  value       = <<-EOT

    =============================================
    OPC AGENT DEPLOYMENT SUMMARY (HR System)
    =============================================

    Deployed Agents:
    %{for k, v in module.opc_agents~}
    - ${k}
      Instance: ${v.instance_id}
      Public IP: ${v.public_ip}
      SSM: ${v.ssm_session_command}
    %{endfor~}

    Shared Security Group: ${aws_security_group.opc_shared.id}

    Next Steps:
    1. Connect to the agent via SSM (command above)
    2. Review /installers/SETUP.md on the host
    3. Install the Okta Provisioning Agent (OPP) + on-prem SCIM/Generic DB connector
    4. Configure the Generic Database Connector app in Okta Admin Console
       (JDBC URL is in SSM: /vita-oig-preview/generic-db/jdbc-url)

    =============================================
  EOT
}
