import sys
import os
print(f"Working directory: {os.getcwd()}")
print(f"sys.path: {sys.path[:3]}")
print(f"\nArchivos en carpeta actual:")
for f in os.listdir("."):
    if f.endswith(".py"):
        print(f"  - {f}")

print("\nIntentando importar aux_correccion_masiva...")
try:
    from aux_correccion_masiva import iniciar_correccion_masiva_completa
    print("✓ Importación exitosa de aux_correccion_masiva")
    
    print("\nIntentando importar corrector_masivo_integrado...")
    from corrector_masivo_integrado import CorrectorMasivoIntegrado
    print("✓ Importación exitosa de corrector_masivo_integrado")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
