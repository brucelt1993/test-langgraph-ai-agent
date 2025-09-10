#!/usr/bin/env python3
"""
Configuration Check Tool

This script provides a command-line interface for checking
and validating the AI Agent configuration.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.startup import run_startup_checks, create_env_template
from app.core.config import settings


async def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Agent Configuration Check Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_config.py --check                Check all configuration
  python check_config.py --check --skip-external   Check config without external APIs
  python check_config.py --template             Create .env.example template
  python check_config.py --show-config          Show current configuration (safe)
        """
    )
    
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Run configuration and connectivity checks"
    )
    parser.add_argument(
        "--skip-external", 
        action="store_true", 
        help="Skip external API connectivity checks"
    )
    parser.add_argument(
        "--template", 
        action="store_true", 
        help="Create .env.example template file"
    )
    parser.add_argument(
        "--show-config", 
        action="store_true", 
        help="Show current configuration (with sensitive data masked)"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Create template
    if args.template:
        create_env_template()
        print("✅ Created .env.example template")
    
    # Show configuration
    if args.show_config:
        print("📋 Current Configuration:")
        config = settings.get_safe_config()
        
        for key, value in config.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)
            
            print(f"  {key}: {value_str}")
    
    # Run checks
    if args.check:
        print("🔍 Running AI Agent configuration checks...\n")
        success = await run_startup_checks(skip_external=args.skip_external)
        
        if success:
            print("\n🎉 All checks passed! Your configuration is ready.")
            return 0
        else:
            print("\n💥 Some checks failed. Please review the errors above.")
            return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)