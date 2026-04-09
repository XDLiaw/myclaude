#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const claudeDir = path.join(process.env.HOME || process.env.USERPROFILE, '.claude');
const settingsPath = path.join(claudeDir, 'settings.json');
const pluginsMdPath = path.join(claudeDir, 'PLUGINS.md');

try {
  const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
  const plugins = settings.enabledPlugins || {};

  const rows = Object.keys(plugins)
    .filter(k => plugins[k])
    .map(id => {
      const [name, registry] = id.split('@');
      return `| ${name} | ${registry} | \`/install ${id}\` |`;
    });

  const content = `# Installed Plugins

換電腦時依此清單重新安裝。

| Plugin | Registry | 安裝指令 |
|--------|----------|----------|
${rows.join('\n')}
`;

  fs.writeFileSync(pluginsMdPath, content, 'utf8');
} catch (e) {
  // silent fail - don't block Claude
}
