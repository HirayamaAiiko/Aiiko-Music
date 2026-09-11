import random
class PlaybackQueue:
    def __init__(self):
        self.tracks = []
        self.current_index = -1
        self.is_shuffled = False
        self.repeat_mode = 0                                         
    def set_queue(self, tracks, start_index=-1):
        self.tracks = list(tracks)
        self.current_index = start_index
    def add_track(self, track):
        self.tracks.append(track)
        if self.current_index == -1:
            self.current_index = 0
    def clear(self):
        if 0 <= self.current_index < len(self.tracks):
            current = self.tracks[self.current_index]
            self.tracks = [current]
            self.current_index = 0
        else:
            self.tracks = []
            self.current_index = -1
    def get_current(self):
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    def get_next(self, manual=False):
        if not self.tracks:
            return None
        if self.repeat_mode == 2 and not manual:
            return self.get_current()
        self.current_index += 1
        if self.current_index >= len(self.tracks):
            if self.repeat_mode == 1:
                self.current_index = 0
                if self.is_shuffled and len(self.tracks) > 1:
                    current = self.tracks[0]
                    self.tracks.pop(0)
                    random.shuffle(self.tracks)
                    self.tracks.insert(0, current)
            else:
                self.current_index = -1
                return None
        return self.get_current()
    def get_prev(self):
        if not self.tracks:
            return None
        self.current_index = max(0, self.current_index - 1)
        return self.get_current()
    def shuffle(self, state=None):
        if state is not None:
            is_turning_on = state
        else:
            is_turning_on = not self.is_shuffled
        self.is_shuffled = is_turning_on
        if self.is_shuffled:
            self.original_tracks = list(self.tracks)
            if len(self.tracks) > 1:
                current = self.get_current()
                if current and current in self.tracks:
                    self.tracks.remove(current)
                    random.shuffle(self.tracks)
                    self.tracks.insert(0, current)
                    self.current_index = 0
                else:
                    random.shuffle(self.tracks)
                    self.current_index = 0
        else:
            if hasattr(self, 'original_tracks'):
                current = self.get_current()
                restored = [t for t in self.original_tracks if t in self.tracks]
                missing = [t for t in self.tracks if t not in self.original_tracks]
                restored.extend(missing)
                self.tracks = restored
                if current and current in self.tracks:
                    self.current_index = self.tracks.index(current)
                else:
                    self.current_index = 0
        return self.is_shuffled
    def set_repeat_mode(self, mode):
        self.repeat_mode = mode % 3
        return self.repeat_mode
    def remove_track(self, track):
        if track in self.tracks:
            index = self.tracks.index(track)
            self.tracks.remove(track)
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                if self.current_index >= len(self.tracks):
                    self.current_index = len(self.tracks) - 1
    def remove_track_by_index(self, index):
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                if self.current_index >= len(self.tracks):
                    self.current_index = len(self.tracks) - 1
    def get_all(self):
        return self.tracks
    def __len__(self):
        return len(self.tracks)
