"""Evita reaplicar históricos al saldo y conserva transferencias normales."""
import os,sys,tempfile
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
os.environ['ATOMO_DATA_DIR']=tempfile.mkdtemp(prefix='atomo-history-check-')
sys.path.insert(0,str(ROOT))
from core.config import LIVE_DB
from core.database import init_db,con,insert_movement,balances_df,positions_df
from core.finance import money,period_summary,ai_context
init_db(LIVE_DB)
today=date.today().isoformat()
with con(LIVE_DB) as c:
 for name,amount in [('A',100),('B',200)]:
  c.execute("INSERT INTO cuentas(nombre,tipo_cuenta,moneda,saldo_base,fecha_saldo_base,creada_en) VALUES (?,'Otra','ARS',?,?,?)",(name,amount,today,today))
 for kind,amount,ori,dst in [('Ingreso',150,None,1),('Gasto',20,2,None),('Transferencia',500,1,2)]:
  c.execute("""INSERT INTO movimientos(fecha,tipo,descripcion,categoria,monto,creado_en,cuenta_origen_id,cuenta_destino_id,importado,impacta_caja,fecha_precision) VALUES (?,?,'Histórico','Otros',?,?,?,?,1,0,'mes')""",(today,kind,amount,today,ori,dst))
assert balances_df(LIVE_DB).sort_values('id').saldo.tolist()==[100,200]
insert_movement(today,'Transferencia','Propia nueva','Transferencia',10,origen=1,destino=2,db=LIVE_DB)
assert balances_df(LIVE_DB).sort_values('id').saldo.tolist()==[90,210]
insert_movement(today,'Ingreso','Ingreso nuevo','Sueldo / ingreso',10,destino=1,db=LIVE_DB)
insert_movement(today,'Gasto','Gasto nuevo','Otros',5,origen=1,db=LIVE_DB)
assert balances_df(LIVE_DB).sort_values('id').saldo.tolist()==[95,210]
s,_=period_summary(today[:7],LIVE_DB);assert s['gastos']==25 and s['ingresos']==160
with con(LIVE_DB) as c:
 c.execute("""INSERT INTO posiciones(cuenta_id,tipo_activo,descripcion,cantidad,precio_promedio,precio_actual,moneda,notas,creada_en,valor_actual_confirmado) VALUES (1,'Otro','Valor desconocido',1,45,0,'ARS','Corroborar',?,0)""",(today,))
assert positions_df(LIVE_DB).precio_actual.isna().all()
assert money(positions_df(LIVE_DB).precio_actual.iloc[0])=='Corroborar'
assert 'valor actual Corroborar' in ai_context(today[:7],LIVE_DB)
print('PASS histórico sin reaplicar saldos, propia nueva sí cambia saldos, ingresos/gastos nuevos y valoración desconocida sin pérdida ficticia.')
