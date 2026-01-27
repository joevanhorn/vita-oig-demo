#!/usr/bin/env python3
"""
cleanup_terraform.py

Cleans up and refactors Terraformer-generated Terraform files:
- Removes tfer-- prefixes
- Removes null values and empty blocks
- Extracts variables
- Organizes resources
- Generates module structure

Usage:
  python3 cleanup_terraform.py --input generated/okta --output cleaned
"""

import argparse
import re
import os
import json
from pathlib import Path
from typing import Dict, List, Set


class TerraformCleaner:
    """Cleans and refactors Terraformer-generated Terraform files"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.variables: Dict[str, Set[str]] = {}
        self.resource_mapping: Dict[str, str] = {}
        
    def clean_resource_name(self, name: str) -> str:
        """Remove tfer-- prefix and sanitize name"""
        # Remove tfer-- prefix
        name = re.sub(r'^tfer--', '', name)
        
        # Replace special characters with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        return name
    
    def extract_variables(self, content: str) -> tuple[str, Dict[str, str]]:
        """Extract hardcoded values that should be variables"""
        variables = {}
        
        # Extract email domains
        email_pattern = r'(["\'])([a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}))\1'
        for match in re.finditer(email_pattern, content):
            email = match.group(2)
            domain = match.group(3)
            var_name = f"email_domain_{domain.replace('.', '_')}"
            variables[var_name] = domain
        
        # Extract organization names
        org_pattern = r'(["\'])([a-z]+-\d+)(\.okta\.com|\.oktapreview\.com)\1'
        for match in re.finditer(org_pattern, content):
            org_name = match.group(2)
            variables['okta_org_name'] = org_name
        
        return content, variables
    
    def remove_null_values(self, content: str) -> str:
        """Remove null value assignments and empty blocks"""
        # Remove lines with null values
        content = re.sub(r'^\s*\w+\s*=\s*null\s*\n', '', content, flags=re.MULTILINE)
        
        # Remove empty blocks
        content = re.sub(r'\n\s*\{\s*\}\s*\n', '\n', content)
        
        # Remove empty lists
        content = re.sub(r'\s*=\s*\[\s*\]\s*\n', '\n', content)
        
        # Remove trailing commas in lists
        content = re.sub(r',(\s*\n\s*[\]\}])', r'\1', content)
        
        return content
    
    def remove_computed_attributes(self, content: str) -> str:
        """Remove computed-only attributes that shouldn't be in config"""
        # Common computed attributes to remove
        computed_attrs = [
            'id',
            'links',
            'logo_url',
            '_links',
            'created',
            'lastUpdated',
            'last_updated',
            'status_changed',
        ]
        
        for attr in computed_attrs:
            # Remove attribute lines
            pattern = rf'^\s*{attr}\s*=.*\n'
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        return content
    
    def clean_terraform_file(self, file_path: Path) -> str:
        """Clean a single Terraform file"""
        print(f"Cleaning: {file_path}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Skip provider.tf files
        if file_path.name == 'provider.tf':
            return content
        
        # Clean resource names
        def replace_resource_name(match):
            resource_type = match.group(1)
            old_name = match.group(2)
            new_name = self.clean_resource_name(old_name)
            
            # Store mapping for cross-references
            old_ref = f"{resource_type}.{old_name}"
            new_ref = f"{resource_type}.{new_name}"
            self.resource_mapping[old_ref] = new_ref
            
            return f'resource "{resource_type}" "{new_name}"'
        
        content = re.sub(
            r'resource\s+"([^"]+)"\s+"([^"]+)"',
            replace_resource_name,
            content
        )
        
        # Remove null values and empty blocks
        content = self.remove_null_values(content)
        
        # Remove computed attributes
        content = self.remove_computed_attributes(content)
        
        # Extract variables
        content, vars_found = self.extract_variables(content)
        for var_name, var_value in vars_found.items():
            if var_name not in self.variables:
                self.variables[var_name] = set()
            self.variables[var_name].add(var_value)
        
        return content
    
    def update_references(self, content: str) -> str:
        """Update resource references to use cleaned names"""
        for old_ref, new_ref in self.resource_mapping.items():
            # Match references like okta_group.tfer--00g123.id
            pattern = re.escape(old_ref) + r'(\.\w+)?'
            replacement = new_ref + r'\1'
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def generate_variables_file(self) -> str:
        """Generate variables.tf content"""
        content = "# Variables extracted from imported resources\n\n"
        
        for var_name, values in sorted(self.variables.items()):
            content += f'variable "{var_name}" {{\n'
            content += f'  description = "Extracted from imported resources"\n'
            content += f'  type        = string\n'
            
            if len(values) == 1:
                content += f'  default     = "{list(values)[0]}"\n'
            
            content += '}\n\n'
        
        return content
    
    def organize_by_resource_type(self):
        """Organize cleaned files by resource type"""
        print("\nOrganizing files by resource type...")
        
        # Map resource types to logical groupings
        resource_groups = {
            'identity': ['okta_user', 'okta_group', 'okta_group_rule'],
            'applications': ['okta_app_oauth', 'okta_app_saml', 'okta_app_basic_auth'],
            'authorization': ['okta_auth_server', 'okta_auth_server_policy', 
                            'okta_auth_server_claim', 'okta_auth_server_scope'],
            'policies': ['okta_policy_mfa', 'okta_policy_password', 'okta_policy_signon'],
            'network': ['okta_network_zone', 'okta_trusted_origin'],
            'schemas': ['okta_user_schema', 'okta_group_schema'],
            'idps': ['okta_idp_saml', 'okta_idp_oidc'],
        }
        
        for group_name, resource_types in resource_groups.items():
            group_dir = self.output_dir / group_name
            group_dir.mkdir(parents=True, exist_ok=True)
            
            # Combine all resources of these types
            combined_content = ""
            
            for resource_type in resource_types:
                resource_dir = self.input_dir / resource_type
                if not resource_dir.exists():
                    continue
                
                for tf_file in resource_dir.glob('*.tf'):
                    if tf_file.name in ['provider.tf', 'outputs.tf', 'variables.tf']:
                        continue
                    
                    cleaned = self.clean_terraform_file(tf_file)
                    combined_content += f"\n# From {tf_file.name}\n"
                    combined_content += cleaned + "\n"
            
            if combined_content:
                output_file = group_dir / f"{group_name}.tf"
                with open(output_file, 'w') as f:
                    f.write(combined_content)
                print(f"Created: {output_file}")
    
    def generate_module_structure(self):
        """Generate a module structure for the imported resources"""
        print("\nGenerating module structure...")
        
        modules_dir = self.output_dir / 'modules'
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main.tf that uses modules
        main_content = """# Main configuration using modules

terraform {
  required_version = ">= 1.9.0"
  
  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.1.0"
    }
  }
}

provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}

# Import existing resources using modules
module "identity" {
  source = "./modules/identity"
  
  okta_org_name = var.okta_org_name
}

module "applications" {
  source = "./modules/applications"
  
  okta_org_name = var.okta_org_name
}

module "policies" {
  source = "./modules/policies"
  
  okta_org_name = var.okta_org_name
}
"""
        
        with open(self.output_dir / 'main.tf', 'w') as f:
            f.write(main_content)
        
        print(f"Created: {self.output_dir / 'main.tf'}")
    
    def create_import_statements(self):
        """Generate terraform import commands for all resources"""
        print("\nGenerating import commands...")
        
        import_script = "#!/bin/bash\n"
        import_script += "# Generated import commands\n\n"
        import_script += "set -e\n\n"
        
        for resource_dir in self.input_dir.iterdir():
            if not resource_dir.is_dir():
                continue
            
            tfstate_file = resource_dir / 'terraform.tfstate'
            if not tfstate_file.exists():
                continue
            
            with open(tfstate_file, 'r') as f:
                state = json.load(f)
            
            for resource in state.get('resources', []):
                resource_type = resource.get('type')
                
                for instance in resource.get('instances', []):
                    resource_name = instance.get('attributes', {}).get('name', 'unknown')
                    resource_id = instance.get('attributes', {}).get('id', '')
                    
                    if resource_id:
                        clean_name = self.clean_resource_name(resource_name)
                        import_script += f'terraform import {resource_type}.{clean_name} {resource_id}\n'
        
        import_file = self.output_dir / 'import_commands.sh'
        with open(import_file, 'w') as f:
            f.write(import_script)
        
        os.chmod(import_file, 0o755)
        print(f"Created: {import_file}")
    
    def run(self):
        """Execute the cleaning process"""
        print("=" * 50)
        print("Terraform Cleaner - Refactoring Generated Code")
        print("=" * 50)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # First pass: clean all files and build resource mapping
        print("\nCleaning Terraform files...")
        for resource_dir in self.input_dir.iterdir():
            if not resource_dir.is_dir():
                continue
            
            for tf_file in resource_dir.glob('*.tf'):
                if tf_file.name == 'provider.tf':
                    continue
                self.clean_terraform_file(tf_file)
        
        # Second pass: update references with cleaned names
        print("\nUpdating resource references...")
        for resource_dir in self.input_dir.iterdir():
            if not resource_dir.is_dir():
                continue
            
            for tf_file in resource_dir.glob('*.tf'):
                if tf_file.name == 'provider.tf':
                    continue
                
                with open(tf_file, 'r') as f:
                    content = f.read()
                
                content = self.update_references(content)
                
                # Write to output directory
                output_subdir = self.output_dir / resource_dir.name
                output_subdir.mkdir(parents=True, exist_ok=True)
                
                with open(output_subdir / tf_file.name, 'w') as f:
                    f.write(content)
        
        # Organize by resource type
        self.organize_by_resource_type()
        
        # Generate variables file
        print("\nGenerating variables.tf...")
        variables_content = self.generate_variables_file()
        with open(self.output_dir / 'variables.tf', 'w') as f:
            f.write(variables_content)
        print(f"Created: {self.output_dir / 'variables.tf'}")
        
        # Generate module structure
        self.generate_module_structure()
        
        # Create import statements
        self.create_import_statements()
        
        # Generate summary
        self.generate_summary()
        
        print("\n" + "=" * 50)
        print("✓ Cleaning completed successfully!")
        print("=" * 50)
    
    def generate_summary(self):
        """Generate a summary of the cleaning process"""
        summary_file = self.output_dir / 'CLEANUP_SUMMARY.md'
        
        content = f"""# Terraform Cleanup Summary

## Overview
Cleaned and refactored Terraformer-generated files from `{self.input_dir}`

## Changes Made

### 1. Resource Names
- Removed `tfer--` prefixes from {len(self.resource_mapping)} resources
- Sanitized resource names to follow Terraform conventions

### 2. Variables Extracted
Extracted {len(self.variables)} variables:
"""
        
        for var_name in sorted(self.variables.keys()):
            content += f"- `{var_name}`\n"
        
        content += """
### 3. Cleanup Actions
- Removed null value assignments
- Removed empty blocks and lists
- Removed computed-only attributes
- Removed trailing commas
- Updated all resource references

### 4. Organization
Files organized by resource type in logical groupings:
- identity/ - Users, groups, and group rules
- applications/ - OAuth and SAML apps
- authorization/ - Auth servers and related resources
- policies/ - MFA, password, and sign-on policies
- network/ - Network zones and trusted origins
- schemas/ - User and group schemas
- idps/ - Identity providers

## Next Steps

1. **Review Generated Files**
   ```bash
   cd """ + str(self.output_dir) + """
   find . -name "*.tf" | head -10
   ```

2. **Update Variables**
   - Edit `variables.tf` with appropriate values
   - Add sensitive flags where needed

3. **Test Configuration**
   ```bash
   terraform init
   terraform plan
   ```

4. **Import Resources (if needed)**
   ```bash
   ./import_commands.sh
   ```

5. **Refine Further**
   - Add locals for repeated values
   - Split large files into smaller modules
   - Add data sources for dynamic lookups
   - Add lifecycle rules where appropriate

## Resource Mapping

Total resources renamed: """ + str(len(self.resource_mapping)) + """

See `resource_mapping.json` for complete mapping of old to new names.
"""
        
        with open(summary_file, 'w') as f:
            f.write(content)
        
        # Save resource mapping as JSON
        mapping_file = self.output_dir / 'resource_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(self.resource_mapping, f, indent=2)
        
        print(f"Created: {summary_file}")
        print(f"Created: {mapping_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean and refactor Terraformer-generated Terraform files"
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input directory containing Terraformer-generated files'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for cleaned files'
    )
    
    args = parser.parse_args()
    
    cleaner = TerraformCleaner(args.input, args.output)
    cleaner.run()


if __name__ == '__main__':
    main()
