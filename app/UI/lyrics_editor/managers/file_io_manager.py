import os
import re
import logging
from core.notification_manager import notify
from core.language_manager import tr
class FileIOManager:
    def __init__(self, track, text_editor):
        self.track = track
        self.text_editor = text_editor
    def load_existing_lyrics(self):
        base_path = os.path.splitext(self.track.filepath)[0]
        valid_exts = ['.lrc', '.srt', '.txt']
        for ext in valid_exts:
            file_path = base_path + ext
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.text_editor.setPlainText(f.read())
                    return True, tr(f"Archivo {ext}")
                except Exception as e:
                    logging.error(f"Error leyendo {ext} existente: {e}")
        try:
            from services.metadata_editor import MetadataEditorService
            props = MetadataEditorService.get_file_properties(self.track.filepath)
            lyrics = props.get('lyrics_sync') or props.get('lyrics_static')
            if lyrics:
                self.text_editor.setPlainText(lyrics)
                return True, tr("Incrustado")
        except Exception as e:
            logging.error(f"Error leyendo metadatos: {e}")
        return False, ""
    def delete_lyrics_file(self):
        base_path = os.path.splitext(self.track.filepath)[0]
        lrc_path = base_path + ".lrc"
        if os.path.exists(lrc_path):
            try:
                os.remove(lrc_path)
                notify.success(tr("Letra eliminada"), tr("Se ha eliminado el archivo .lrc correctamente."), parent=self.text_editor.window())
                self.text_editor.clear()
                return True
            except Exception as e:
                notify.error(tr("Error"), tr(f"No se pudo eliminar el archivo:\n{e}"), parent=self.text_editor.window())
                return False
        return False
    def save_lyrics_file(self):
        text = self.text_editor.toPlainText().strip()
        base_path = os.path.splitext(self.track.filepath)[0]
        lrc_path = base_path + ".lrc"
        if not text:
            if os.path.exists(lrc_path):
                try:
                    os.remove(lrc_path)
                except Exception as e:
                    logging.error(f"Error borrando LRC: {e}")
            return True
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return True
        except Exception as e:
            notify.error(tr("Error al Guardar"), f"{tr('No se pudo crear el archivo:')}\n{e}", parent=self.text_editor.window())
            return False
    def embed_lyrics_to_file(self):
        text = self.text_editor.toPlainText().strip()
        if not text:
            notify.warning(tr("Sin Letras"), tr("No hay letras para incrustar."), parent=self.text_editor.window())
            return False
        from services.metadata_editor import MetadataEditorService
        is_synced = bool(re.search(r'\[\d{2}:\d{2}', text))
        metadata = {}
        if is_synced:
            metadata['lyrics_sync'] = text
            clean_text = re.sub(r'\[\s*\d+:\d+(?:\.\d+)?\s*\]', '', text)
            clean_lines = [line.strip() for line in clean_text.split('\n')]
            metadata['lyrics_static'] = '\n'.join(clean_lines).strip()
        else:
            metadata['lyrics_static'] = text
        try:
            MetadataEditorService.save_metadata(self.track.filepath, metadata)
            if os.path.exists(self.track.filepath):
                self.track.mtime = os.path.getmtime(self.track.filepath)
                from database import save_batch
                save_batch([self.track])
            notify.success(tr("¡Incrustado!"), tr("Las letras se han guardado dentro del archivo original."), parent=self.text_editor.window())
            return True
        except Exception as e:
            logging.error(f"Error incrustando letras: {e}")
            notify.error(tr("Error"), tr("No se pudieron incrustar las letras en este archivo de audio."), parent=self.text_editor.window())
            return False