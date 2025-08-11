#!/bin/bash
# Script d'installation automatique du correctif ALMAA Phase 2

echo "🔧 Installation du correctif ALMAA Phase 2..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "main_phase2.py" ]; then
    echo "❌ Erreur: main_phase2.py non trouvé. Lancez ce script depuis le répertoire ALMAA."
    exit 1
fi

# Backup
echo "💾 Sauvegarde des fichiers existants..."
cp -r agents agents_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "⚠️ Pas d'agents à sauvegarder"
cp -r core core_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "⚠️ Pas de core à sauvegarder"  
cp main_phase2.py main_phase2_backup_$(date +%Y%m%d_%H%M%S).py 2>/dev/null || echo "⚠️ Pas de main_phase2.py à sauvegarder"

# Installation
echo "🚀 Installation des correctifs..."

# Créer répertoires si nécessaire
mkdir -p agents/special agents/mixins core

# Copier les fichiers corrigés
cp almaa_phase2_final_fix/agents/special/moderator.py agents/special/ && echo "✅ moderator.py installé"
cp almaa_phase2_final_fix/agents/mixins/debater.py agents/mixins/ && echo "✅ debater.py installé"
cp almaa_phase2_final_fix/core/debate_manager.py core/ && echo "✅ debate_manager.py installé"
cp almaa_phase2_final_fix/agents/enhanced_chef.py agents/ && echo "✅ enhanced_chef.py installé"
cp almaa_phase2_final_fix/main_phase2.py . && echo "✅ main_phase2.py installé"

echo "🎉 Installation terminée!"
echo ""
echo "🧪 Test rapide:"
echo "python main_phase2.py interactive"
echo ""
echo "📋 Question de test:"
echo 'tu pourrais en faire un débat de cette question : "Quelle est la meilleure architecture pour un système de paiement haute disponibilité ?"'
