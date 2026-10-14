import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
import tempfile
import unittest
from pathlib import Path
import duckdb
from retail_pipeline.pipeline import ingest, validate
from retail_pipeline.config import ROOT
from retail_pipeline.prepare import COLUMNS

class PipelineTests(unittest.TestCase):
    def test_incremental_returns_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'input.csv'
            rows = [
                ['100','A','Product',2,'2010-01-01 10:00:00',5,1,'UK'],
                ['100','A','Product',2,'2010-01-01 10:00:00',5,1,'UK'],
                ['C101','A','Product',-1,'2010-10-01 10:00:00',5,None,'UK'],
                ['102','M','Manual',1,'2010-10-02 10:00:00',20,1,'UK'],
                ['103','A','Product',1,'2010-10-02 10:00:00',-5,1,'UK'],
                ['104','A','Product',1,'not-a-date',5,1,'UK'],
                ['105','B','BANK CHARGES',1,'2010-10-02 10:00:00',5,1,'UK']]
            with path.open('w',newline='') as out:
                writer=csv.writer(out); writer.writerow(COLUMNS); writer.writerows(rows)
            with duckdb.connect() as conn:
                first=ingest(conn,str(path)); self.assertEqual(first['new_rows'],6)
                second=ingest(conn,str(path)); self.assertEqual(second['new_rows'],0)
                conn.execute((ROOT/'code/sql/transform.sql').read_text())
                self.assertFalse(any(validate(conn).values()))
                self.assertEqual(conn.execute('SELECT count(*) FROM analytics.fact_sales').fetchone()[0],2)
                self.assertEqual(float(conn.execute('SELECT sum(total_price) FROM analytics.fact_sales').fetchone()[0]),5)
                with path.open('a',newline='') as out:
                    csv.writer(out).writerow(['106','A','Product',3,'2010-10-03 10:00:00',5,2,'UK'])
                self.assertEqual(ingest(conn,str(path))['new_rows'],1)
    def test_missing_schema_fails(self):
        with tempfile.TemporaryDirectory() as directory, duckdb.connect() as conn:
            path=Path(directory)/'bad.csv'; path.write_text('unexpected\n1\n')
            with self.assertRaises(ValueError):
                ingest(conn,str(path))

if __name__=='__main__':
    unittest.main()
