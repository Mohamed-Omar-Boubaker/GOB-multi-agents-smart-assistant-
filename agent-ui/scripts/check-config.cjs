/**
 * Script de vérification de la configuration
 * Usage: npm run check
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Vérification configuration mobile...\n');

const checks = {
  passed: [],
  failed: [],
  warnings: []
};

// Vérifier fichiers essentiels
const requiredFiles = [
  'vite.config.ts',
  'src/config/api.config.ts',
  'src/services/permissions.service.ts',
  'src/services/api.ts',
  'src/App.tsx',
  'package.json'
];

console.log('📁 Vérification fichiers...');
requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, '..', file);
  if (fs.existsSync(filePath)) {
    checks.passed.push(`✅ ${file}`);
  } else {
    checks.failed.push(`❌ ${file} MANQUANT`);
  }
});

// Vérifier vite.config.ts
console.log('\n⚙️ Vérification vite.config.ts...');
try {
  const viteConfig = fs.readFileSync(
    path.join(__dirname, '..', 'vite.config.ts'),
    'utf-8'
  );

  if (viteConfig.includes("base: './'")) {
    checks.passed.push("✅ base: './' configuré");
  } else {
    checks.failed.push("❌ base: './' MANQUANT dans vite.config.ts");
  }

  if (viteConfig.includes('outDir')) {
    checks.passed.push("✅ outDir configuré");
  } else {
    checks.warnings.push("⚠️ outDir non configuré (optionnel)");
  }
} catch (error) {
  checks.failed.push("❌ Impossible de lire vite.config.ts");
}

// Vérifier api.config.ts
console.log('\n🔌 Vérification api.config.ts...');
try {
  const apiConfig = fs.readFileSync(
    path.join(__dirname, '..', 'src/config/api.config.ts'),
    'utf-8'
  );

  if (apiConfig.includes('192.168.1.10') && apiConfig.includes('⚠️ REMPLACER')) {
    checks.warnings.push('⚠️ IP locale par défaut (192.168.1.10) - À MODIFIER avec votre vraie IP');
  } else if (apiConfig.includes('192.168.')) {
    checks.passed.push('✅ IP locale configurée');
  } else {
    checks.failed.push('❌ Configuration IP locale manquante');
  }

  if (apiConfig.includes('isCapacitor')) {
    checks.passed.push('✅ Détection Capacitor implémentée');
  }
} catch (error) {
  checks.failed.push("❌ Impossible de lire api.config.ts");
}

// Vérifier package.json
console.log('\n📦 Vérification package.json...');
try {
  const packageJson = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf-8')
  );

  if (packageJson.scripts && packageJson.scripts['build:mobile']) {
    checks.passed.push('✅ Script build:mobile disponible');
  } else {
    checks.warnings.push('⚠️ Script build:mobile manquant');
  }

  // Vérifier si node_modules existe
  if (fs.existsSync(path.join(__dirname, '..', 'node_modules'))) {
    checks.passed.push('✅ node_modules présent');
  } else {
    checks.failed.push('❌ node_modules manquant - Lancer: npm install');
  }
} catch (error) {
  checks.failed.push("❌ Impossible de lire package.json");
}

// Vérifier si dist existe (après build)
console.log('\n🏗️ Vérification build...');
if (fs.existsSync(path.join(__dirname, '..', 'dist'))) {
  checks.passed.push('✅ Dossier dist/ existe (build déjà effectué)');
} else {
  checks.warnings.push('⚠️ Dossier dist/ n\'existe pas - Lancer: npm run build');
}

// Afficher résultats
console.log('\n' + '='.repeat(60));
console.log('📊 RÉSULTATS DE LA VÉRIFICATION\n');

if (checks.passed.length > 0) {
  console.log('✅ SUCCÈS:');
  checks.passed.forEach(check => console.log('  ' + check));
  console.log('');
}

if (checks.warnings.length > 0) {
  console.log('⚠️  AVERTISSEMENTS:');
  checks.warnings.forEach(check => console.log('  ' + check));
  console.log('');
}

if (checks.failed.length > 0) {
  console.log('❌ ERREURS:');
  checks.failed.forEach(check => console.log('  ' + check));
  console.log('');
}

console.log('='.repeat(60));

// Résumé et prochaines étapes
if (checks.failed.length === 0) {
  console.log('\n✅ Configuration COMPLÈTE! Prêt pour mobile.\n');
  
  console.log('📋 PROCHAINES ÉTAPES:\n');
  console.log('1. Configurez votre IP locale dans src/config/api.config.ts');
  console.log('   - Trouvez votre IP avec: ipconfig');
  console.log('   - Cherchez "Adresse IPv4" (ex: 192.168.1.10)');
  console.log('');
  console.log('2. Lancez le backend Python:');
  console.log('   cd ../backend');
  console.log('   uvicorn main:app --host 0.0.0.0 --port 8000');
  console.log('');
  console.log('3. Testez le build:');
  console.log('   npm run build');
  console.log('');
  console.log('4. Installez Capacitor:');
  console.log('   npm install @capacitor/core @capacitor/cli @capacitor/android');
  console.log('   npx cap init');
  console.log('');
  
  process.exit(0);
} else {
  console.log(`\n❌ ${checks.failed.length} erreur(s) à corriger\n`);
  process.exit(1);
}
