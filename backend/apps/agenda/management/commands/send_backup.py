import os
import subprocess
import zipfile
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings

class Command(BaseCommand):
    help = 'Gera o backup do banco de dados, compacta em zip e envia por e-mail'

    def handle(self, *args, **kwargs):
        today_str = datetime.now().strftime('%Y-%m-%d')
        zip_filename = f"backup_salao_pro_{today_str}.zip"
        dump_filename = f"dump_{today_str}.sql"
        
        db_settings = settings.DATABASES['default']
        engine = db_settings.get('ENGINE', '')
        
        self.stdout.write(f"Iniciando backup. Engine detectada: {engine}")
        
        try:
            if 'postgresql' in engine:
                self.stdout.write("Gerando dump do PostgreSQL...")
                db_name = db_settings.get('NAME')
                db_user = db_settings.get('USER')
                db_password = db_settings.get('PASSWORD')
                db_host = db_settings.get('HOST', 'localhost')
                db_port = str(db_settings.get('PORT', '5432'))
                
                env = os.environ.copy()
                if db_password:
                    env['PGPASSWORD'] = db_password
                    
                dump_cmd = [
                    'pg_dump',
                    '-h', db_host,
                    '-p', db_port,
                    '-U', db_user,
                    '-F', 'c', # Formato custom (compactado) ou plain text 'p'
                    '-f', dump_filename,
                    db_name
                ]
                
                # Executa o comando
                process = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
                if process.returncode != 0:
                    self.stderr.write(f"Erro no pg_dump: {process.stderr}")
                    return
                
                file_to_zip = dump_filename
                
            elif 'sqlite3' in engine:
                self.stdout.write("Copiando banco de dados SQLite...")
                db_path = str(db_settings.get('NAME'))
                dump_filename = f"db_backup_{today_str}.sqlite3"
                shutil.copy2(db_path, dump_filename)
                file_to_zip = dump_filename
                
            else:
                self.stderr.write(f"Engine de banco de dados não suportada para backup automático: {engine}")
                return
                
            # Compactando em ZIP
            self.stdout.write(f"Compactando arquivo em {zip_filename}...")
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_to_zip, arcname=os.path.basename(file_to_zip))
                
            # Envio de e-mail
            email_to = 'infor@salaopro.site'
            subject = f"✅ Backup Diário Salão_PRO - {today_str}"
            body = "Segue em anexo o backup do banco de dados do Salão_PRO.\n\nEste é um e-mail automático, não responda."
            
            self.stdout.write(f"Enviando e-mail para {email_to}...")
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_to]
            )
            email.attach_file(zip_filename)
            email.send(fail_silently=False)
            
            self.stdout.write(self.style.SUCCESS('E-mail enviado com sucesso!'))
            
        except Exception as e:
            self.stderr.write(f"Ocorreu um erro durante o backup: {str(e)}")
            
        finally:
            # Limpeza dos arquivos locais
            self.stdout.write("Limpando arquivos temporários...")
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            if 'dump_filename' in locals() and os.path.exists(dump_filename):
                os.remove(dump_filename)
            self.stdout.write(self.style.SUCCESS('Rotina de backup concluída.'))
