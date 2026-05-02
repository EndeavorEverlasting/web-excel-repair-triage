import openpyxl
from openpyxl.utils import get_column_letter

class TrackerTooling:
    def __init__(self, template_path=None):
        self.template_path = template_path

    def correct_dupdeployed_formula(self, file_path, output_path=None):
        """
        Corrects the DupDeployed formula to ensure that a duplicate is only flagged
        if the same identifier is Deployed="YES" in a DIFFERENT location.
        Locations are derived from Current Building (G), Area/Unit/Dept (I), and Room (J).
        Identifiers checked: V, W, X, Y, AB, AH, AP, AQ.
        """
        if output_path is None:
            output_path = file_path

        wb = openpyxl.load_workbook(file_path)
        if 'Deployments' not in wb.sheetnames:
            print("Error: 'Deployments' sheet not found.")
            return False
            
        ws = wb['Deployments']
        max_row = ws.max_row
        
        # Columns mapped
        # B = Deployed
        # F = DupDeployed
        # G = Current Building, I = Area/Unit/Dept, J = Room
        # ID columns: V, W, X, Y, AB, AH, AP, AQ
        
        id_cols = ['V', 'W', 'X', 'Y', 'AB', 'AH', 'AP', 'AQ']
        
        for row in range(2, max_row + 1):
            # Construct the complex OR condition
            conditions = []
            for c in id_cols:
                # If MAC address, strip colons and dashes
                if c in ['Y', 'AH']:
                    val_expr = f'UPPER(SUBSTITUTE(SUBSTITUTE(TRIM(${c}{row}),":",""),"-",""))'
                    range_expr = f'UPPER(SUBSTITUTE(SUBSTITUTE(TRIM(${c}$2:${c}${max_row}),":",""),"-",""))'
                else:
                    val_expr = f'UPPER(TRIM(${c}{row}))'
                    range_expr = f'UPPER(TRIM(${c}$2:${c}${max_row}))'

                cond = (
                    f'AND(${c}{row}<>"", LOWER(TRIM(${c}{row}))<>"n/a", LOWER(TRIM(${c}{row}))<>"na", '
                    f'SUMPRODUCT(--({range_expr}={val_expr}), '
                    f'--(UPPER(TRIM($B$2:$B${max_row}))="YES"), '
                    f'--(UPPER(TRIM($G$2:$G${max_row})&TRIM($I$2:$I${max_row})&TRIM($J$2:$J${max_row}))<>UPPER(TRIM($G{row})&TRIM($I{row})&TRIM($J{row}))))>0)'
                )
                conditions.append(cond)
                
            or_statement = "OR(" + ", ".join(conditions) + ")"
            
            formula = f'=IF(UPPER(TRIM($B{row}))<>"YES","", IF({or_statement}, "Yes", "No"))'
            ws[f'F{row}'] = formula

        wb.save(output_path)
        print(f"Successfully updated DupDeployed formula and saved to {output_path}")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tracker Tooling")
    parser.add_argument("--fix-duplicates", dest="fix_dup", help="Path to tracker to fix DupDeployed formula")
    parser.add_argument("--out", help="Output path")
    args = parser.parse_args()
    
    tool = TrackerTooling()
    if args.fix_dup:
        tool.correct_dupdeployed_formula(args.fix_dup, args.out)
