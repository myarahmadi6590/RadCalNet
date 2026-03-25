import numpy as np
import xml.etree.ElementTree as ET
from matplotlib.colors import ListedColormap
from pathlib import Path

from SBG.HelperFunctions.functions import get_rsr

# %% Sites and Sensors Config

def get_config():
    helperfile_dir = Path(__file__).resolve().parent / "HelperFiles"
    XML_dir = helperfile_dir / "XMLs"
    RSR_dir = helperfile_dir / "RSRs"
    sites_config = read_xml(XML_dir / "SitesConfig.xml")
    sensors_config = build_sensors_config(read_xml(XML_dir / "SensorsConfig.xml"), RSR_dir)
    return sites_config, sensors_config

def read_xml(xml_path):
    root = ET.parse(xml_path).getroot()
    items = {}
    for item in root:
        attrs = item.attrib.copy()
        for k, t in {"lat": float, "lon": float, "slice_size": int}.items():
            if k in attrs:
                attrs[k] = t(attrs[k])
        items[item.tag] = attrs
    return items

def build_sensors_config(sensors, RSR_dir, max_workers=None):
    sensors_config = {}
    for sensor, item in sensors.items():
        rsr_files = get_rsr(Path(RSR_dir) / item["portal"] / sensor, "txt")
        sensors_config[sensor] = {"portal": item.get("portal"),
                                  "version": item.get("version"),
                                  "file_type": item.get("file_type"),
                                  "source": item.get("source"),
                                  "bands": {},}
        for file in rsr_files:
            args = (sensor, item.get("portal"), item.get("version"), item.get("file_type"), item.get("source"), file)
            sensor_name, band_info = _process_rsr_file(args)
            band = band_info.pop("band")
            sensors_config[sensor_name]["bands"][band] = band_info
    return sensors_config

def _process_rsr_file(args):
    sensor, portal, version, file_type, source, file = args
    rsr_data = np.loadtxt(file, delimiter="\t", encoding="utf-8-sig")
    cw, bw = compute_band_metrics(rsr_data)
    band, name, res = file.stem.split("_")
    return (sensor, {"band": band, "name": name, "res": int(res), "cw": round(float(cw), 1), "bw": round(float(bw), 1),},)

def compute_band_metrics(rsr_data):
    wl = rsr_data[:,0]
    rsr = rsr_data[:,1]
    center = np.sum(wl * rsr) / np.sum(rsr)
    half = np.max(rsr) / 2
    idx = np.where(rsr >= half)[0]
    bandwidth = wl[idx[-1]] - wl[idx[0]]
    return center, bandwidth


# %% Plot Config

def get_plot_config():
    xml_path = Path(__file__).resolve().parent.parent / "HelperFiles" / "XMLs" / "PlotConfig.xml"
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return {'cmap': create_wavelength_cmap(),
            'param_keys': parse_keys('ParamKeys', root),
            'site_quality_keys': parse_keys('SiteQualityKeys', root),
            'angles_keys': parse_keys('AnglesKeys', root),
            'record_time_keys': parse_keys('RecordTimeKeys', root),
            'metadata_quality_keys': parse_keys('MetadataQualityKeys', root)}

def create_wavelength_cmap(wl_min=400, wl_max=2500, step=0.1):
    def vis_rgb(w):
        if w < 440: r,g,b = -(w-440)/40,0,1
        elif w < 490: r,g,b = 0,(w-440)/50,1
        elif w < 510: r,g,b = 0,1,-(w-510)/20
        elif w < 580: r,g,b = (w-510)/70,1,0
        elif w < 645: r,g,b = 1,-(w-645)/65,0
        else: r,g,b = 1,0,0
        return tuple(c**0.8 for c in (r,g,b))
    def wl_rgb(w):
        if w <= 700: return vis_rgb(w)
        if w <= 1000:
            t=(w-700)/300; return (1-0.5*t,0.2-0.1*t,0.6+0.2*t)
        if w <= 1700:
            t=(w-1000)/700; return (0.2,0.7+0.1*t,0.9-0.5*t)
        t=(w-1700)/800
        return (0.72-0.32*t,0.46-0.06*t,0.20+0.25*t)
    wls = np.arange(wl_min, wl_max+step, step)
    return ListedColormap([wl_rgb(w) for w in wls], name="wavelength_cmap")

def parse_keys(section_name, root):
    result = {}
    for key in root.find(section_name):
        name = key.attrib['name']
        value = key.attrib.get('value', name)
        result[name] = value
    return result