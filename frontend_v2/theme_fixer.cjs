const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, 'src');

function walk(dir) {
    let results = [];
    const list = fs.readdirSync(dir);
    list.forEach(file => {
        file = path.join(dir, file);
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) { 
            results = results.concat(walk(file));
        } else { 
            if (file.endsWith('.jsx') || file.endsWith('.js') || file.endsWith('.css')) {
                results.push(file);
            }
        }
    });
    return results;
}

const files = walk(srcDir);

files.forEach(file => {
    let content = fs.readFileSync(file, 'utf8');
    let original = content;

    // Dark layout backgrounds
    content = content.replace(/bg-slate-900(?=[\s"'])/g, 'bg-white');
    content = content.replace(/bg-slate-800(?=[\s"'])/g, 'bg-slate-50');
    content = content.replace(/bg-slate-950\/50/g, 'bg-white');
    content = content.replace(/bg-slate-800\/50/g, 'bg-white');
    
    // Borders
    content = content.replace(/border-white\/10/g, 'border-slate-200');
    content = content.replace(/border-white\/5/g, 'border-slate-200');
    content = content.replace(/border-slate-700/g, 'border-slate-300');
    content = content.replace(/hover:border-white\/20/g, 'hover:border-slate-400');
    
    // Texts
    content = content.replace(/text-slate-200/g, 'text-slate-700');
    content = content.replace(/text-slate-300/g, 'text-slate-600');
    content = content.replace(/text-slate-400/g, 'text-slate-500');
    content = content.replace(/text-slate-50(?=[\s"'])/g, 'text-slate-900');
    
    // Blues to Slate (Premium Black-and-White theme)
    content = content.replace(/text-blue-400/g, 'text-slate-900');
    content = content.replace(/text-blue-500/g, 'text-slate-900');
    content = content.replace(/text-blue-300/g, 'text-slate-700');
    
    content = content.replace(/bg-blue-500\/10/g, 'bg-slate-100');
    content = content.replace(/bg-blue-500\/5/g, 'bg-slate-50');
    content = content.replace(/bg-blue-500\/20/g, 'bg-slate-100');
    
    // We intentionally ignore replacing inside buttons if they are bg-white that was converted.
    // However, if we do bg-blue-500 -> bg-slate-900, we get dark buttons, which is good.
    content = content.replace(/bg-blue-500(?=[\s"'\/])/g, 'bg-slate-900');
    content = content.replace(/bg-blue-600/g, 'bg-slate-800');
    content = content.replace(/hover:bg-blue-600/g, 'hover:bg-slate-800');
    content = content.replace(/hover:bg-blue-700/g, 'hover:bg-slate-800');
    
    // Gradients
    content = content.replace(/from-blue-400/g, 'from-slate-800');
    content = content.replace(/to-indigo-300/g, 'to-slate-600');
    content = content.replace(/from-blue-600/g, 'from-slate-900');
    content = content.replace(/to-indigo-600/g, 'to-slate-800');
    content = content.replace(/to-indigo-500/g, 'to-slate-700');
    content = content.replace(/hover:to-indigo-700/g, 'hover:to-slate-900');
    
    // Borders & Rings
    content = content.replace(/border-blue-500/g, 'border-slate-900');
    content = content.replace(/focus:border-blue-500/g, 'focus:border-slate-900');
    content = content.replace(/focus:ring-blue-500/g, 'focus:ring-slate-900');
    content = content.replace(/ring-blue-500/g, 'ring-slate-900');
    content = content.replace(/hover:border-blue-500\/30/g, 'hover:border-slate-300');
    
    // Shadows
    content = content.replace(/shadow-blue-[^\s"']+/g, 'shadow-sm');
    
    if (content !== original) {
        fs.writeFileSync(file, content, 'utf8');
        console.log('Updated:', file);
    }
});
