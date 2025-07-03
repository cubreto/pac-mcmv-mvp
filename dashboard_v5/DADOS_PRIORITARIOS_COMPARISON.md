# Dados Prioritários - Source vs Database Comparison

## Expected (Excel Source) vs Current Database

### Excel Source File: `Dados_Prioritários_Janeiro_Abril_2025.xlsx`
| Modalidade | Linhas (Projetos) | UH Contratadas | UH Entregues | UH Vigentes |
|------------|------------------:|---------------:|-------------:|------------:|
| FAR        |        **17,314** |  **5,302,607** | **4,620,204** | **663,963** |
| FDS        |         **2,307** |    **310,974** |   **157,628** | **153,346** |
| RURAL      |        **32,855** |    **789,852** |   **692,778** |  **96,622** |
| **Total**  |        **52,476** |  **6,403,433** | **5,470,610** | **913,931** |

### Current Database (`mcmv_v2.dados_prioritarios`)
| Modalidade | Linhas (Projetos) | UH Contratadas | UH Entregues | UH Vigentes |
|------------|------------------:|---------------:|-------------:|------------:|
| FAR        |        **17,314** |  **5,284,167** | **4,620,204** | **663,963** |
| FDS        |         **2,307** |    **310,974** |   **157,628** | **153,346** |
| RURAL      |        **32,855** |    **789,400** |   **692,778** |  **96,622** |
| **Total**  |        **52,476** |  **6,384,541** | **5,470,610** | **913,931** |

## Analysis

### ✅ **Perfect Matches:**
- **Project counts**: All programs match exactly (17,314 + 2,307 + 32,855 = 52,476)
- **UH Entregues**: All programs match exactly 
- **UH Vigentes**: All programs match exactly
- **Total UH Entregues**: 5,470,610 ✅
- **Total UH Vigentes**: 913,931 ✅

### ⚠️ **Discrepancies:**

#### **FAR Program:**
- Expected UH Contratadas: **5,302,607**
- Current UH Contratadas: **5,284,167**
- **Difference: -18,440 UH** ❌

#### **RURAL Program:**
- Expected UH Contratadas: **789,852**
- Current UH Contratadas: **789,400**
- **Difference: -452 UH** ❌

#### **Total UH Contratadas:**
- Expected Total: **6,403,433**
- Current Total: **6,384,541**
- **Total Difference: -18,892 UH** ❌

## Root Cause Analysis

The issue is likely in how **UH Contratadas** is calculated in our ETL process.

### Current Logic (Incorrect):
```sql
SUM(COALESCE(uh_entregues, 0) + COALESCE(uh_vigentes, 0))::INTEGER as uh_contratadas
```

### Expected Logic (From Excel):
The Excel file has **UH Contratadas** as a direct column, not a calculated field.

## Required Fix

1. **Use the literal `uh_contratadas` column** from the source data instead of calculating it
2. **Verify the ETL mapping** to ensure we're using the correct source column
3. **Update the SQL query** to use the direct column value

## Verification

The expected totals exactly match what Julio provided, confirming that our database should reproduce these numbers exactly.