# Instrucciones para Resolver Conflictos en GitHub PR

## ⚠️ PROBLEMA
La rama `main` tiene una versión CON `pandas-ta` que **falla en GitHub Actions**.
Nuestra rama tiene la versión SIN `pandas-ta` que **funciona correctamente**.

## ✅ SOLUCIÓN
En el PR de GitHub, cuando veas conflictos, **usa SIEMPRE los archivos de esta rama** (claude/setup-tradolympo-structure-0e5O4).

## Archivos en Conflicto

### 1. `bot.py`
**Usar:** Nuestra versión (esta rama)
- ✅ NO usa `import pandas_ta as ta`
- ✅ Usa `calcular_rsi()` y `calcular_sma()` (funciones nativas)
- ✅ Línea 10: "Séptima modificación: Arquitectura modular SIN pandas-ta"

### 2. `requirements.txt`
**Usar:** Nuestra versión (esta rama)
```txt
# Alpaca Trading Bot Dependencies
alpaca-trade-api==3.0.2
pytz==2024.1
```
- ✅ NO debe tener `pandas-ta==0.3.14b0`

### 3. `watchlist.json`
**Usar:** Nuestra versión (esta rama)
- Formato más simple sin `account_settings`

## Cómo Resolver en GitHub

1. Ve al PR en GitHub
2. Click en "Resolve conflicts"
3. Para CADA archivo en conflicto:
   - Busca las marcas `<<<<<<<` y `>>>>>>>`
   - **Elimina TODO el bloque entre `======= y >>>>>>main`**
   - **Mantén solo el código entre `<<<<<<< claude/setup... y =======`**
   - Elimina las marcas `<<<<<<<` y `=======`
4. Click "Mark as resolved"
5. Click "Commit merge"

## Verificación Final

Después del merge, verifica:
```bash
grep "pandas-ta" requirements.txt  # Debe dar: NO encontrado
grep "pandas_ta" bot.py  # Debe dar: NO encontrado
```

