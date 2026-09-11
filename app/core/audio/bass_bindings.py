import os
import sys
import logging
import ctypes
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
BASS_POS_BYTE           = 0
BASS_ACTIVE_STOPPED     = 0
BASS_ACTIVE_PLAYING     = 1
BASS_ACTIVE_STALLED     = 2
BASS_ACTIVE_PAUSED      = 3
BASS_ACTIVE_PAUSED_DEVICE = 4
BASS_ATTRIB_VOL         = 2
BASS_ATTRIB_FREQ        = 1
BASS_SLIDE_LOG          = 0x1000000
BASS_SYNC_END           = 2
BASS_SYNC_ONETIME       = 0x80000000
BASS_UNICODE            = 0x80000000
BASS_SAMPLE_FLOAT       = 256
BASS_CONFIG_BUFFER       = 0
BASS_CONFIG_UPDATEPERIOD = 6
BASS_DATA_FFT1024        = 0x80000002
BASS_DATA_FFT4096        = 0x80000004
BASS_DATA_FFT8192        = 0x80000005
BASS_DATA_FFT16384       = 0x80000006
BASS_STREAM_DECODE      = 0x200000
BASS_STREAM_PRESCAN     = 0x20000
BASS_MIXER_END          = 0x10000
BASS_MIXER_NONSTOP      = 0x20000
BASS_MIXER_DOWNMIX      = 0x400000
BASS_MIXER_PAUSE        = 0x20000                                                    
BASS_MIXER_CHAN_PAUSE    = 0x20000                                 
BASS_MIXER_NORAMPIN      = 0x800000                          
BASS_MIXER_BUFFER        = 0x2000                                              
class BASS_DEVICEINFO(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("driver", ctypes.c_char_p),
        ("flags", ctypes.c_ulong)
    ]
SYNCPROC = ctypes.CFUNCTYPE(None, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p)
WASAPIPROC = ctypes.CFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p)
BASS_WASAPI_EXCLUSIVE = 1
BASS_WASAPI_AUTOFORMAT = 2
BASS_WASAPI_BUFFER = 4
BASS_FX_DX8_PARAMEQ = 7
BASS_FX_BFX_PEAKEQ = 0x10004
BASS_BFX_CHANALL = -1
class BASS_DX8_PARAMEQ(ctypes.Structure):
    _fields_ = [
        ("fCenter", ctypes.c_float),
        ("fBandwidth", ctypes.c_float),
        ("fGain", ctypes.c_float)
    ]
class BASS_BFX_PEAKEQ(ctypes.Structure):
    _fields_ = [
        ("lBand", ctypes.c_int),
        ("fBandwidth", ctypes.c_float),
        ("fQ", ctypes.c_float),
        ("fCenter", ctypes.c_float),
        ("fGain", ctypes.c_float),
        ("lChannel", ctypes.c_int)
    ]
def _load_bassmix_dll():
    from config import APP_ROOT
    import os
    libs_dir = os.path.join(APP_ROOT, "libs")
    mix_path = os.path.join(libs_dir, "bassmix.dll")
    if not os.path.exists(mix_path):
        return None
    dll = ctypes.WinDLL(mix_path)
    dll.BASS_Mixer_StreamCreate.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_Mixer_StreamCreate.restype = ctypes.c_ulong
    dll.BASS_Mixer_StreamAddChannel.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_Mixer_StreamAddChannel.restype = ctypes.c_bool
    dll.BASS_Mixer_StreamAddChannelEx.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_uint64, ctypes.c_uint64]
    dll.BASS_Mixer_StreamAddChannelEx.restype = ctypes.c_bool
    dll.BASS_Mixer_ChannelSetPosition.argtypes = [ctypes.c_ulong, ctypes.c_uint64, ctypes.c_ulong]
    dll.BASS_Mixer_ChannelSetPosition.restype = ctypes.c_bool
    dll.BASS_Mixer_ChannelGetPosition.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_Mixer_ChannelGetPosition.restype = ctypes.c_uint64
    dll.BASS_Mixer_ChannelRemove.argtypes = [ctypes.c_ulong]
    dll.BASS_Mixer_ChannelRemove.restype = ctypes.c_bool
    dll.BASS_Mixer_ChannelFlags.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_Mixer_ChannelFlags.restype = ctypes.c_ulong
    dll.BASS_Mixer_ChannelSetSync.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_uint64, SYNCPROC, ctypes.c_void_p]
    dll.BASS_Mixer_ChannelSetSync.restype = ctypes.c_ulong
    dll.BASS_Mixer_ChannelRemoveSync.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_Mixer_ChannelRemoveSync.restype = ctypes.c_bool
    return dll
def _load_bass_dll():
    from config import APP_ROOT
    libs_dir = os.path.join(APP_ROOT, "libs")
    bass_path = os.path.join(libs_dir, "bass.dll")
    if not os.path.exists(bass_path):
        raise FileNotFoundError(f"No se encontró bass.dll en: {bass_path}")
    os.environ["PATH"] = libs_dir + ";" + os.environ.get("PATH", "")
    dll = ctypes.WinDLL(bass_path)
    dll.BASS_Init.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    dll.BASS_Init.restype = ctypes.c_bool
    dll.BASS_Free.restype = ctypes.c_bool
    dll.BASS_SetConfig.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_SetConfig.restype = ctypes.c_bool
    dll.BASS_PluginLoad.argtypes = [ctypes.c_char_p, ctypes.c_ulong]
    dll.BASS_PluginLoad.restype = ctypes.c_ulong
    dll.BASS_StreamCreateFile.argtypes = [ctypes.c_bool, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_ulong]
    dll.BASS_StreamCreateFile.restype = ctypes.c_ulong
    dll.BASS_StreamFree.argtypes = [ctypes.c_ulong]
    dll.BASS_StreamFree.restype = ctypes.c_bool
    dll.BASS_ChannelPlay.argtypes = [ctypes.c_ulong, ctypes.c_bool]
    dll.BASS_ChannelPlay.restype = ctypes.c_bool
    dll.BASS_ChannelPause.argtypes = [ctypes.c_ulong]
    dll.BASS_ChannelPause.restype = ctypes.c_bool
    dll.BASS_ChannelStop.argtypes = [ctypes.c_ulong]
    dll.BASS_ChannelStop.restype = ctypes.c_bool
    dll.BASS_ChannelIsActive.argtypes = [ctypes.c_ulong]
    dll.BASS_ChannelIsActive.restype = ctypes.c_ulong
    dll.BASS_ChannelGetPosition.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_ChannelGetPosition.restype = ctypes.c_uint64
    dll.BASS_ChannelGetLength.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_ChannelGetLength.restype = ctypes.c_uint64
    dll.BASS_ChannelBytes2Seconds.argtypes = [ctypes.c_ulong, ctypes.c_uint64]
    dll.BASS_ChannelBytes2Seconds.restype = ctypes.c_double
    dll.BASS_ChannelSeconds2Bytes.argtypes = [ctypes.c_ulong, ctypes.c_double]
    dll.BASS_ChannelSeconds2Bytes.restype = ctypes.c_uint64
    dll.BASS_ChannelSetPosition.argtypes = [ctypes.c_ulong, ctypes.c_uint64, ctypes.c_ulong]
    dll.BASS_ChannelSetPosition.restype = ctypes.c_bool
    dll.BASS_ChannelGetData.argtypes = [ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong]
    dll.BASS_ChannelGetData.restype = ctypes.c_ulong
    dll.BASS_ChannelBytes2Seconds.argtypes = [ctypes.c_ulong, ctypes.c_uint64]
    dll.BASS_ChannelBytes2Seconds.restype = ctypes.c_double
    dll.BASS_ChannelSeconds2Bytes.argtypes = [ctypes.c_ulong, ctypes.c_double]
    dll.BASS_ChannelSeconds2Bytes.restype = ctypes.c_uint64
    dll.BASS_ChannelSetAttribute.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float]
    dll.BASS_ChannelSetAttribute.restype = ctypes.c_bool
    dll.BASS_ChannelGetAttribute.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_float)]
    dll.BASS_ChannelGetAttribute.restype = ctypes.c_bool
    dll.BASS_ChannelSlideAttribute.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float, ctypes.c_ulong]
    dll.BASS_ChannelSlideAttribute.restype = ctypes.c_bool
    dll.BASS_ChannelIsSliding.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_ChannelIsSliding.restype = ctypes.c_bool
    dll.BASS_ChannelSetSync.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_uint64, SYNCPROC, ctypes.c_void_p]
    dll.BASS_ChannelSetSync.restype = ctypes.c_ulong
    dll.BASS_ChannelRemoveSync.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_ChannelRemoveSync.restype = ctypes.c_bool
    dll.BASS_ErrorGetCode.restype = ctypes.c_int
    dll.BASS_GetDeviceInfo.argtypes = [ctypes.c_ulong, ctypes.POINTER(BASS_DEVICEINFO)]
    dll.BASS_GetDeviceInfo.restype = ctypes.c_bool
    dll.BASS_SetDevice.argtypes = [ctypes.c_ulong]
    dll.BASS_SetDevice.restype = ctypes.c_bool
    dll.BASS_ChannelSetDevice.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_ChannelSetDevice.restype = ctypes.c_bool
    dll.BASS_ChannelSetFX.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int]
    dll.BASS_ChannelSetFX.restype = ctypes.c_ulong
    dll.BASS_ChannelRemoveFX.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
    dll.BASS_ChannelRemoveFX.restype = ctypes.c_bool
    dll.BASS_FXSetParameters.argtypes = [ctypes.c_ulong, ctypes.c_void_p]
    dll.BASS_FXSetParameters.restype = ctypes.c_bool
    dll.BASS_FXGetParameters.argtypes = [ctypes.c_ulong, ctypes.c_void_p]
    dll.BASS_FXGetParameters.restype = ctypes.c_bool
    return dll
def _load_bass_fx_dll():
    from config import APP_ROOT
    import os
    libs_dir = os.path.join(APP_ROOT, "libs")
    fx_path = os.path.join(libs_dir, "bass_fx.dll")
    if not os.path.exists(fx_path):
        return None
    dll = ctypes.WinDLL(fx_path)
    dll.BASS_FX_GetVersion.restype = ctypes.c_ulong
    return dll
def _load_basswasapi_dll():
    from config import APP_ROOT
    import os
    libs_dir = os.path.join(APP_ROOT, "libs")
    wasapi_path = os.path.join(libs_dir, "basswasapi.dll")
    if not os.path.exists(wasapi_path):
        return None
    dll = ctypes.WinDLL(wasapi_path)
    dll.BASS_WASAPI_Init.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float, ctypes.c_float, WASAPIPROC, ctypes.c_void_p]
    dll.BASS_WASAPI_Init.restype = ctypes.c_bool
    dll.BASS_WASAPI_Start.argtypes = []
    dll.BASS_WASAPI_Start.restype = ctypes.c_bool
    dll.BASS_WASAPI_Stop.argtypes = [ctypes.c_bool]
    dll.BASS_WASAPI_Stop.restype = ctypes.c_bool
    dll.BASS_WASAPI_Free.argtypes = []
    dll.BASS_WASAPI_Free.restype = ctypes.c_bool
    dll.BASS_WASAPI_GetDeviceInfo.argtypes = [ctypes.c_ulong, ctypes.POINTER(BASS_DEVICEINFO)]
    dll.BASS_WASAPI_GetDeviceInfo.restype = ctypes.c_bool
    dll.BASS_WASAPI_SetDevice.argtypes = [ctypes.c_ulong]
    dll.BASS_WASAPI_SetDevice.restype = ctypes.c_bool
    dll.BASS_WASAPI_GetData.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    dll.BASS_WASAPI_GetData.restype = ctypes.c_ulong
    return dll