import time
import random
from datetime import datetime
from core.language_manager import tr
from UI.user_profile_widget import is_birthday_today
class GreetingManager:
    @staticmethod
    def get_greeting(name: str, accent_hex: str) -> tuple[str, str, bool]:
        name_html = f'<font color="{accent_hex}">{name}</font>'
        now = datetime.now()
        month, day = now.month, now.day
        hour = now.hour
        special_greeting = None
        if month == 1 and day == 1:
            special_greeting = tr("¡Feliz Año Nuevo!")
        elif month == 2 and day == 14:
            special_greeting = tr("¡Feliz San Valentín!")
        elif month == 10 and day == 31:
            special_greeting = tr("¡Feliz Halloween!")
        elif month == 12 and day == 24:
            special_greeting = tr("¡Feliz Nochebuena!")
        elif month == 12 and day == 25:
            special_greeting = tr("¡Feliz Navidad!")
        elif month == 12 and day == 31:
            special_greeting = tr("¡Feliz Nochevieja!")
        is_special_day = False
        if special_greeting:
            title = f"{special_greeting} {name_html}"
            sub = tr("Un día perfecto para tus canciones favoritas.")
            if (month == 12 and day in (24, 25, 31)) or (month == 1 and day == 1):
                is_special_day = True
        elif is_birthday_today():
            title = tr("¡Feliz Cumpleaños!")
            sub = tr("¡Que tengas un día increíble, {name}!").format(name=name_html)
            is_special_day = True
        else:
            if 5 <= hour < 12:
                greeting = tr("Buenos días")
            elif 12 <= hour < 19:
                greeting = tr("Buenas tardes")
            else:
                greeting = tr("Buenas noches")
            title = f"{greeting}, {name_html}"
            sub = tr("Tu biblioteca está lista.")
        return title, sub, is_special_day
    @staticmethod
    def get_dynamic_subtitle(data: dict, accent_hex: str) -> str:
        now = datetime.now()
        stats = data.get("stats", {})
        weekly = data.get("weekly", {})
        playlist_info = data.get("playlist_info")
        recent_history = data.get("recent_history")
        subs = []
        subs.append(tr("¿Qué escuchamos hoy?"))
        subs.append(tr("Tu biblioteca está lista."))
        subs.append(tr("Una canción puede ser suficiente."))
        subs.append(tr("Hoy también hay música."))
        subs.append(tr("Todo lo que necesitas está aquí."))
        subs.append(tr("Tu colección sigue creciendo."))
        subs.append(tr("¿Volvemos a una vieja favorita?"))
        subs.append(tr("Sin algoritmo. Tú eliges."))
        if stats.get("total_tracks", 0) > 0:
            count_fmt = f'<font color="{accent_hex}">{stats["total_tracks"]}</font>'
            subs.append(tr("{count} canciones listas para reproducir.").format(count=count_fmt))
        if weekly.get("total_ms", 0) > 0:
            hours = int(weekly["total_ms"] // 3600000)
            if hours > 0:
                hrs_fmt = f'<font color="{accent_hex}">{hours}</font>'
                subs.append(tr("Has escuchado {count} horas esta semana.").format(count=hrs_fmt))
        is_music_day = (now.month == 10 and now.day == 1) or (now.month == 6 and now.day == 21)
        if is_music_day:
            return tr("Hoy es el Día de la Música · Una buena excusa para volver a tus favoritas.")
        if playlist_info:
            dur_ms = playlist_info["duration_ms"]
            total_seconds = dur_ms / 1000
            h = int(total_seconds // 3600)
            m = int((total_seconds % 3600) // 60)
            dur_str = f"{h} h {m} min" if h > 0 else f"{m} min"
            pl_name = f'<font color="{accent_hex}">{playlist_info.get("name", "Favoritas")}</font>'
            pl_cnt = f'<font color="{accent_hex}">{playlist_info["count"]}</font>'
            pl_dur = f'<font color="{accent_hex}">{dur_str}</font>'
            subs.append(tr("Tu playlist {name} te espera · {count} canciones · {dur}").format(name=pl_name, count=pl_cnt, dur=pl_dur))
        if recent_history and len(recent_history) > 0:
            track_info = recent_history[0]
            days_since_app_used = track_info.get("days_since_app_used", 0)
            days_since_prev_play = track_info.get("days_since_prev_play", 0)
            if days_since_app_used > 3:
                subs.append(tr("Qué bueno verte de nuevo · Tu música sigue aquí."))
            elif days_since_prev_play > 14:
                title_fmt = f'<font color="{accent_hex}">{track_info["title"]}</font>'
                subs.append(tr("Ha pasado un tiempo · {title} vuelve a sonar.").format(title=title_fmt))
        random.seed(now.hour)
        chosen_sub = random.choice(subs)
        random.seed()        
        return chosen_sub