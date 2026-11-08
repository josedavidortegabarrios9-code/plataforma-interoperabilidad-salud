import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hsb.parser import HL7Parser, CSVParser

class TestParserContracts(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    def test_01_adt_a01_valido_sede2(self):
        filepath = os.path.join(self.fixtures_dir, "01_adt_a01_valido_sede2.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        data, reasons = HL7Parser.validate_and_extract_hl7(content)
        self.assertEqual(len(reasons), 0, f"No debió tener errores: {reasons}")
        self.assertEqual(data["documento"], "1007")
        self.assertEqual(data["sede"], 2)
        self.assertEqual(data["cod_cie10"], "J45.9")
        self.assertEqual(data["sexo"], "F")

    def test_02_oru_r01_laboratorio_sede1(self):
        filepath = os.path.join(self.fixtures_dir, "02_oru_r01_laboratorio_sede1.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        data, reasons = HL7Parser.validate_and_extract_hl7(content)
        self.assertEqual(len(reasons), 0, f"No debió tener errores: {reasons}")
        self.assertEqual(data["documento"], "1001")
        self.assertEqual(data["sede"], 1)
        self.assertIsNotNone(data["observacion"])
        self.assertEqual(data["observacion"]["cod_loinc"], "718-7")
        self.assertEqual(data["observacion"]["valor"], 13.8)

    def test_03_adt_a01_invalido_motivos(self):
        filepath = os.path.join(self.fixtures_dir, "03_adt_a01_invalido.hl7")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        data, reasons = HL7Parser.validate_and_extract_hl7(content)
        self.assertGreater(len(reasons), 0, "Debió ser rechazado")
        self.assertIn("documento no numérico", reasons)
        self.assertIn("sexo no válido", reasons)
        self.assertIn("diagnóstico sin mapeo a CIE-10", reasons)

    def test_04_csv_sede3(self):
        filepath = os.path.join(self.fixtures_dir, "04_sede3_legado.csv")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        
        header = lines[0]
        rows = lines[1:]
        entregados = []
        rechazados = []

        for idx, row in enumerate(rows, start=1):
            data, reasons = CSVParser.parse_line(row, idx)
            if not reasons:
                entregados.append(data["documento"])
            else:
                rechazados.append((data["documento"] if data else f"row-{idx}", reasons))

        # Según LEEME.md: 3 entregados (1008, 1009, 1010) y 2 rechazados
        self.assertEqual(entregados, ["1008", "1009", "1010"])
        self.assertEqual(len(rechazados), 2)
        # Rechazo 1011 (DOLOR MISTERIOSO sin mapeo)
        self.assertEqual(rechazados[0][0], "1011")
        self.assertIn("dx sin mapeo", rechazados[0][1])
        # Rechazo 12 (documento de 2 dígitos)
        self.assertEqual(rechazados[1][0], "12")
        self.assertIn("documento de 2 dígitos o no numérico", rechazados[1][1])

if __name__ == "__main__":
    unittest.main()
