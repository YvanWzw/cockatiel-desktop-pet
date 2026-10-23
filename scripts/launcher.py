"""PyInstaller entry point; absolute imports work in both frozen and source runs."""
from cockatiel_pet.app import main

raise SystemExit(main())
