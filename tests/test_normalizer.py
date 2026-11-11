import unittest
import sys
import os

# Asegurar import de fhir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fhir.normalizer import FHIRNormalizer

class TestFHIRNormalizer(unittest.TestCase):
    def test_01_build_patient_valido(self):
        pat = FHIRNormalizer.build_patient(
            doc="1007",
            nombre="Andrea",
            apellido="Rojas",
            fecha_nac="19900214",
            sexo="F",
            sede="Cartagena"
        )
        self.assertEqual(pat["resourceType"], "Patient")
        self.assertEqual(pat["id"], "pac-1007")
        self.assertEqual(pat["gender"], "female")
        self.assertEqual(pat["birthDate"], "1990-02-14")
        self.assertEqual(pat["identifier"][0]["value"], "1007")

    def test_02_build_encounter_valido(self):
        enc = FHIRNormalizer.build_encounter(
            encounter_id="S2-0101",
            doc="1007",
            fecha_ingreso="20261107101500",
            clase="E",
            medico="Dr. Mateo Ruiz",
            sede="Cartagena"
        )
        self.assertEqual(enc["resourceType"], "Encounter")
        self.assertEqual(enc["id"], "enc-S2-0101")
        self.assertEqual(enc["class"]["code"], "AMB")
        self.assertEqual(enc["subject"]["reference"], "Patient/pac-1007")

    def test_03_build_condition_cie10(self):
        cond = FHIRNormalizer.build_condition(
            cond_id="101",
            doc="1007",
            encounter_id="S2-0101",
            cod_cie10="J45.9",
            desc_cie10="Asma",
            fecha="2026-11-07"
        )
        self.assertEqual(cond["resourceType"], "Condition")
        self.assertEqual(cond["id"], "cond-101")
        self.assertEqual(cond["code"]["coding"][0]["code"], "J45.9")
        self.assertEqual(cond["code"]["coding"][0]["system"], "http://hl7.org/fhir/sid/icd-10")
        self.assertEqual(cond["subject"]["reference"], "Patient/pac-1007")

    def test_04_build_observation_loinc(self):
        obs = FHIRNormalizer.build_observation(
            obs_id="S1-0150",
            doc="1001",
            encounter_id="S1-0150",
            cod_loinc="718-7",
            desc_loinc="Hemoglobina",
            valor=13.8,
            unidad="g/dL"
        )
        self.assertEqual(obs["resourceType"], "Observation")
        self.assertEqual(obs["code"]["coding"][0]["code"], "718-7")
        self.assertEqual(obs["valueQuantity"]["value"], 13.8)
        self.assertEqual(obs["valueQuantity"]["unit"], "g/dL")

    def test_05_bundle_transaction_idempotente(self):
        pat = FHIRNormalizer.build_patient("1007", "Andrea", "Rojas", "19900214", "F", "Cartagena")
        enc = FHIRNormalizer.build_encounter("S2-0101", "1007", "2026-11-07T10:15:00", "E", "Dr. Mateo Ruiz")
        bundle = FHIRNormalizer.build_transaction_bundle([pat, enc])
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "transaction")
        self.assertEqual(len(bundle["entry"]), 2)
        # Verificar método PUT determinista
        self.assertEqual(bundle["entry"][0]["request"]["method"], "PUT")
        self.assertEqual(bundle["entry"][0]["request"]["url"], "Patient/pac-1007")

    def test_06_caso_invalido_genero_o_formato(self):
        # Verificar mapeo seguro de género ante entradas atípicas
        pat = FHIRNormalizer.build_patient("9999", "Prueba", "Error", None, "X", "Central")
        self.assertEqual(pat["gender"], "other")
        self.assertIsNone(pat["birthDate"])

if __name__ == "__main__":
    unittest.main()
