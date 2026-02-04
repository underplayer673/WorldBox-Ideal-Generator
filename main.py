import customtkinter as ctk
import os
import json
import zlib
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

# === НАСТРОЙКИ ===
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# ==========================================
# ОКНО "ХИРУРГА" (РЕДАКТОР СОСТАВА JSON)
# ==========================================
class SaveSurgeonWindow(ctk.CTkToplevel):
    def __init__(self, parent, data, callback, lang="ru"):
        super().__init__(parent)
        self.data = data
        self.callback = callback
        self.lang = lang
        
        # СЛОВАРЬ ХИРУРГА
        self.loc = {
            "ru": {
                "title": "WorldBox Save Surgeon (Редактор состава)",
                "header": "АНАЛИЗ ФАЙЛА СОХРАНЕНИЯ",
                "desc": "Настройте фильтры для каждого списка данных",
                "btn_cancel": "Отмена",
                "btn_gen": "СГЕНЕРИРОВАТЬ ФАЙЛ",
                "map_lock": "[Массив Карты: Вкл/Выкл]",
                # Опции
                "opt_all": "Все (100%)",
                "opt_light": "Легкая (Убрать мусор)",
                "opt_strong": "Сильная (Топ-50)",
                "opt_extreme": "Экстрим (Топ-15)",
                "opt_live": "Только живые",
                "opt_vip": "Только важные (VIP)",
                "opt_kings": "Только Короли"
            },
            "en": {
                "title": "WorldBox Save Surgeon (Content Editor)",
                "header": "SAVE FILE ANALYSIS",
                "desc": "Configure filters for each data list",
                "btn_cancel": "Cancel",
                "btn_gen": "GENERATE FILE",
                "map_lock": "[Map Array: On/Off]",
                # Options
                "opt_all": "All (100%)",
                "opt_light": "Light (No Trash)",
                "opt_strong": "Strong (Top-50)",
                "opt_extreme": "Extreme (Top-15)",
                "opt_live": "Only Living",
                "opt_vip": "Only Important (VIP)",
                "opt_kings": "Only Kings"
            }
        }
        
        txt = self.loc[self.lang]
        self.title(txt["title"])
        self.geometry("950x750")
        self.resizable(True, True)
        
        ctk.CTkLabel(self, text=txt["header"], font=("Segoe UI", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text=txt["desc"], text_color="gray").pack(pady=(0, 10))

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.settings = {}
        self.build_ui()

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text=txt["btn_cancel"], fg_color="#550000", hover_color="#330000", command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=txt["btn_gen"], fg_color="#006600", hover_color="#004400", 
                      font=("Segoe UI", 16, "bold"), command=self.on_confirm).pack(side="right", fill="x", expand=True, padx=10)

    def build_ui(self):
        txt = self.loc[self.lang]
        
        raw_stats = []
        total_size = 0
        for k, v in self.data.items():
            s_len = len(json.dumps(v, ensure_ascii=False))
            raw_stats.append((k, s_len))
            total_size += s_len
        
        if total_size == 0: total_size = 1
        raw_stats.sort(key=lambda x: x[1], reverse=True)

        BINARY_ONLY = ["tileArray", "tileAmounts", "tiles", "hmap", "hmap_1", "hmap_2", "hmap_3", "wmap", "mmap", "water_map"]

        for key, size in raw_stats:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2, padx=5)

            is_kept = True
            if key in ["tiles", "hmap", "wmap", "water_map"]: is_kept = False
            
            chk_var = ctk.BooleanVar(value=is_kept)
            chk = ctk.CTkCheckBox(row, text=f'"{key}"', variable=chk_var, font=("Consolas", 14, "bold"), width=220)
            chk.pack(side="left")

            percent = (size / total_size) * 100
            size_str = f"{size/(1024*1024):.2f} MB" if size > 1024*1024 else f"{size/1024:.1f} KB"
            stat_color = "#FF5555" if percent > 20 else ("#FFAA00" if percent > 5 else "gray")
            
            ctk.CTkLabel(row, text=f"{size_str} ({percent:.1f}%)", text_color=stat_color, width=150, anchor="e").pack(side="left", padx=10)

            opt_var = ctk.StringVar(value=txt["opt_all"])
            
            if isinstance(self.data[key], list):
                if key in BINARY_ONLY:
                    ctk.CTkLabel(row, text=txt["map_lock"], text_color="gray").pack(side="right", padx=20)
                    opt_var = None 
                else:
                    opts = [txt["opt_all"], txt["opt_light"], txt["opt_strong"], txt["opt_extreme"]]
                    
                    if key == "actors_data": 
                        opts = [txt["opt_all"], txt["opt_live"], txt["opt_vip"], txt["opt_kings"]]
                    
                    ctk.CTkOptionMenu(row, values=opts, variable=opt_var, width=200).pack(side="right")
            else:
                opt_var = None

            self.settings[key] = {"chk": chk_var, "opt": opt_var}

    def on_confirm(self):
        final_cfg = {}
        for k, v in self.settings.items():
            final_cfg[k] = {"keep": v["chk"].get(), "mode": v["opt"].get() if v["opt"] else None}
        self.callback(final_cfg)
        self.destroy()


# ==========================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ==========================================
class WorldBoxFinalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ЛОКАЛИЗАЦИЯ
        self.lang_code = "ru"
        self.loc = {
            "ru": {
                "window_title": "WorldBox Generator v7.2 (Final Complete)",
                "header": "Генератор Идеала v7.2",
                "desc": "Полный парсер + Редактор 'Хирург' + Режимы",
                "path_prefix": "Папка: ",
                "not_found": "Не найдена",
                "browse": "Обзор...",
                "combo_default": "...",
                "folder_missing": "Папка saves не найдена",
                "folder_empty": "В папке пусто",
                "slot": "Слот",
                "found_msg": "Найдено {} сохранений",
                "btn_start": "СОЗДАТЬ ОТЧЕТ",
                "status_wait": "Ожидание...",
                "status_unpack": "Распаковка...",
                "status_json": "Чтение JSON...",
                "status_filter": "Обработка (Режим: {})...",
                "status_done": "Готово!",
                "status_error": "Ошибка!",
                "msg_success_title": "Успех",
                "msg_success_text": "Файл сохранен:\n{}",
                "msg_error_title": "Ошибка",
                "unknown": "Неизвестный",
                "nature": "Природа",
                "record": " (РЕКОРД)",
                "antirecord": " (АНТИРЕКОРД)",
                "file_not_found": "Файл сохранения не найден!",
                "modes": ["КАСТОМ (ХИРУРГ)", "Айсберг (RAW)", "Гигантская (Smart)", "Классическая (Original)", "Мини (Top-15)", "Ультра (Abstract)"],
                "mode_label": "Режим генерации:",
                "surgeon_proc": "Выполнение операции..."
            },
            "en": {
                "window_title": "WorldBox Generator v7.2 (Final Complete)",
                "header": "Ideal Generator v7.2",
                "desc": "Full Parser + Surgeon Editor + Modes",
                "path_prefix": "Path: ",
                "not_found": "Not found",
                "browse": "Browse...",
                "combo_default": "...",
                "folder_missing": "Saves folder not found",
                "folder_empty": "Folder is empty",
                "slot": "Slot",
                "found_msg": "Found {} saves",
                "btn_start": "CREATE REPORT",
                "status_wait": "Waiting...",
                "status_unpack": "Unpacking...",
                "status_json": "Reading JSON...",
                "status_filter": "Processing (Mode: {})...",
                "status_done": "Done!",
                "status_error": "Error!",
                "msg_success_title": "Success",
                "msg_success_text": "File saved:\n{}",
                "msg_error_title": "Error",
                "unknown": "Unknown",
                "nature": "Nature",
                "record": " (RECORD)",
                "antirecord": " (ANTI-RECORD)",
                "file_not_found": "Save file not found!",
                "modes": ["CUSTOM (SURGEON)", "Iceberg (RAW)", "Giant (Smart)", "Classic (Original)", "Mini (Top-15)", "Ultra (Abstract)"],
                "mode_label": "Mode:",
                "surgeon_proc": "Performing surgery..."
            }
        }

        self.title(self.get_text("window_title"))
        self.geometry("600x650")
        self.resizable(False, False)
        self.saves_path = self.detect_saves_path()
        self.downloads_path = str(Path.home() / "Downloads")
        self.setup_ui()
        self.scan_saves()

    def get_text(self, key): return self.loc[self.lang_code].get(key, key)

    def change_language(self, value):
        self.lang_code = value.lower()
        self.title(self.get_text("window_title"))
        self.lbl_title.configure(text=self.get_text("header"))
        self.lbl_desc.configure(text=self.get_text("desc"))
        self.btn_browse.configure(text=self.get_text("browse"))
        self.btn_start.configure(text=self.get_text("btn_start"))
        self.lbl_status.configure(text=self.get_text("status_wait"))
        self.lbl_mode.configure(text=self.get_text("mode_label"))
        
        cur_modes = self.get_text("modes")
        self.combo_mode.configure(values=cur_modes)
        self.combo_mode.set(cur_modes[3])

        path_text = self.saves_path if self.saves_path else self.get_text("not_found")
        self.lbl_path.configure(text=f"{self.get_text('path_prefix')}{path_text[-30:] if self.saves_path else path_text}")
        self.scan_saves()

    def detect_saves_path(self):
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            path = os.path.join(user_profile, r'AppData\LocalLow\mkarpenko\WorldBox\saves')
            if os.path.exists(path): return path
        return None

    def setup_ui(self):
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.lang_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.lang_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.lang_switch = ctk.CTkSegmentedButton(self.lang_frame, values=["RU", "EN"], command=self.change_language, width=60)
        self.lang_switch.set("RU") 
        self.lang_switch.pack(side="right")

        self.lbl_title = ctk.CTkLabel(self.frame, text=self.get_text("header"), font=("Segoe UI", 26, "bold"))
        self.lbl_title.pack(pady=(5, 5))
        self.lbl_desc = ctk.CTkLabel(self.frame, text=self.get_text("desc"), text_color="gray")
        self.lbl_desc.pack(pady=(0, 20))

        self.path_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.path_frame.pack(fill="x", padx=20)
        path_display = self.saves_path if self.saves_path else self.get_text("not_found")
        self.lbl_path = ctk.CTkLabel(self.path_frame, text=f"{self.get_text('path_prefix')}{path_display}", anchor="w")
        self.lbl_path.pack(side="left", fill="x", expand=True)
        self.btn_browse = ctk.CTkButton(self.path_frame, text=self.get_text("browse"), width=80, command=self.browse_folder)
        self.btn_browse.pack(side="right")

        self.combo_saves = ctk.CTkOptionMenu(self.frame, values=[self.get_text("combo_default")], width=300, height=40, font=("Segoe UI", 14))
        self.combo_saves.pack(pady=(20, 10))

        self.lbl_mode = ctk.CTkLabel(self.frame, text=self.get_text("mode_label"), font=("Segoe UI", 12))
        self.lbl_mode.pack(pady=(10, 0))
        modes = self.get_text("modes")
        self.combo_mode = ctk.CTkOptionMenu(self.frame, values=modes, width=300, height=30, fg_color="#444")
        self.combo_mode.set(modes[3]) 
        self.combo_mode.pack(pady=(5, 20))

        self.btn_start = ctk.CTkButton(self.frame, text=self.get_text("btn_start"), command=self.run_thread, 
                                       width=250, height=60, font=("Segoe UI", 18, "bold"), 
                                       fg_color="#107C10", hover_color="#0b5a0b")
        self.btn_start.pack(pady=10)

        self.lbl_status = ctk.CTkLabel(self.frame, text=self.get_text("status_wait"), text_color="gray")
        self.lbl_status.pack(side="bottom", pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.saves_path = folder
            prefix = self.get_text("path_prefix")
            self.lbl_path.configure(text=f"{prefix}...{folder[-30:]}")
            self.scan_saves()

    def scan_saves(self):
        if not self.saves_path or not os.path.exists(self.saves_path):
            self.combo_saves.configure(values=[self.get_text("folder_missing")])
            self.btn_start.configure(state="disabled")
            return

        found = []
        slot_word = self.get_text("slot")
        for i in range(1, 61):
            if os.path.exists(os.path.join(self.saves_path, f"save{i}", "map.wbox")) or \
               os.path.exists(os.path.join(self.saves_path, f"save{i}", "map.json")):
                found.append(f"{slot_word} {i}")
        if found:
            self.combo_saves.configure(values=found)
            self.combo_saves.set(found[0])
            self.btn_start.configure(state="normal")
            self.lbl_status.configure(text=self.get_text("found_msg").format(len(found)), text_color="#3498db")
        else:
            self.combo_saves.configure(values=[self.get_text("folder_empty")])
            self.btn_start.configure(state="disabled")

    def run_thread(self):
        threading.Thread(target=self.process_save).start()

    def process_save(self):
        selection = self.combo_saves.get()
        mode_text = self.combo_mode.get()
        slot_word = self.get_text("slot")
        
        if slot_word not in selection and "Slot" not in selection and "Слот" not in selection: 
            return

        self.btn_start.configure(state="disabled")
        try:
            slot_num = selection.split(" ")[1]
            slot_folder = os.path.join(self.saves_path, f"save{slot_num}")
            wbox_path = os.path.join(slot_folder, "map.wbox")
            json_path = os.path.join(slot_folder, "map.json")
            
            data = None
            if os.path.exists(wbox_path):
                self.lbl_status.configure(text=self.get_text("status_unpack"), text_color="orange")
                with open(wbox_path, "rb") as f:
                    file_content = f.read()
                    try: data = json.loads(zlib.decompress(file_content))
                    except zlib.error: data = json.loads(file_content)
            elif os.path.exists(json_path):
                self.lbl_status.configure(text=self.get_text("status_json"), text_color="orange")
                with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
            else:
                raise FileNotFoundError(self.get_text("file_not_found"))

            # ID РЕЖИМА
            current_modes = self.get_text("modes")
            mode_idx = current_modes.index(mode_text) if mode_text in current_modes else 3

            # КАСТОМ (ХИРУРГ)
            if mode_idx == 0:
                self.after(0, lambda: SaveSurgeonWindow(self, data, lambda cfg: self.run_surgeon_thread(data, slot_num, cfg), lang=self.lang_code))
                return

            self.lbl_status.configure(text=self.get_text("status_filter").format(mode_text), text_color="#3498db")
            
            if mode_idx == 1: # Айсберг
                final_path = self.save_raw_dump(data, slot_num, "Iceberg", clean_maps=False)
            elif mode_idx == 2: # Гигант
                final_path = self.save_raw_dump(data, slot_num, "Giant", clean_maps=True)
            else: # Classic, Mini, Ultra
                final_path = self.apply_exact_algorithm(data, slot_num, mode_idx)

            self.finish_process(final_path)

        except Exception as e:
            self.lbl_status.configure(text=self.get_text("status_error"), text_color="red")
            messagebox.showerror(self.get_text("msg_error_title"), str(e))
            self.btn_start.configure(state="normal")

    def run_surgeon_thread(self, data, slot_num, config):
        threading.Thread(target=self.apply_surgeon, args=(data, slot_num, config)).start()

    def apply_surgeon(self, data, slot, config):
        try:
            self.lbl_status.configure(text=self.get_text("surgeon_proc"), text_color="#AA00AA")
            keys_to_del = []
            
            for k, settings in config.items():
                if not settings["keep"]:
                    keys_to_del.append(k)
                    continue
                
                mode = str(settings["mode"]) # Convert to string to match keywords safely
                val = data[k]
                if not isinstance(val, list): continue
                
                # --- УМНАЯ СОРТИРОВКА (Работает для обоих языков) ---
                if k == "cities" and ("Сильная" in mode or "Strong" in mode or "Экстрим" in mode or "Extreme" in mode):
                    val.sort(key=lambda x: x.get("created_time", 0))
                
                if k == "kingdoms" and ("Сильная" in mode or "Strong" in mode or "Экстрим" in mode or "Extreme" in mode):
                    val.sort(key=lambda x: x.get("created_time", 0))

                if k == "clans": val.sort(key=lambda x: x.get("units_count", 0), reverse=True)
                if k == "cultures": val.sort(key=lambda x: x.get("renown", 0), reverse=True)
                if k == "languages": val.sort(key=lambda x: x.get("speakers_new", 0), reverse=True)

                # --- ЛОГИКА ОБРЕЗКИ (Проверяем и RU, и EN ключевые слова) ---
                
                # 1. LIGHT / ЛЕГКАЯ
                if "Легкая" in mode or "Light" in mode:
                    if k == "families": data[k] = [x for x in val if x.get("count", 0) > 0]
                    elif k == "wars": data[k] = [x for x in val if not x.get("ended", False)]
                
                # 2. STRONG / СИЛЬНАЯ
                elif "Сильная" in mode or "Strong" in mode:
                    if k == "actors_data":
                        data[k] = [x for x in val if (x.get("favorite") or x.get("s_kills", 0) > 0 or x.get("level", 1) > 1)]
                    else: # Top 50
                        data[k] = val[:50]
                
                # 3. EXTREME / ЭКСТРИМ
                elif "Экстрим" in mode or "Extreme" in mode:
                    if k == "actors_data":
                        data[k] = [x for x in val if (x.get("favorite") or x.get("king", False))]
                    else: # Top 15
                        data[k] = val[:15]
                
                # 4. СПЕЦ. ОПЦИИ АКТЕРОВ
                elif "живые" in mode or "Living" in mode:
                     pass # Worldbox обычно чистит мертвых, но можно добавить проверку HP > 0
                elif "важные" in mode or "Important" in mode:
                     data[k] = [x for x in val if (x.get("favorite") or x.get("s_kills", 0) > 0)]
                elif "Короли" in mode or "Kings" in mode:
                     data[k] = [x for x in val if x.get("favorite")]

            for k in keys_to_del: del data[k]

            path = self.save_raw_dump(data, slot, "Custom")
            self.finish_process(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.btn_start.configure(state="normal")

    def finish_process(self, path):
        self.lbl_status.configure(text=self.get_text("status_done"), text_color="#2CC985")
        messagebox.showinfo(self.get_text("msg_success_title"), self.get_text("msg_success_text").format(os.path.basename(path)))
        self.btn_start.configure(state="normal")

    def save_raw_dump(self, data, slot_num, prefix, clean_maps=False):
        if clean_maps:
            keys = ["tiles", "tileArray", "tileAmounts", "hmap", "hmap_1", "hmap_2", "hmap_3", "water_map", "wmap", "mmap"]
            for k in keys: 
                if k in data: del data[k]
            if "mapStats" in data:
                for k in keys:
                    if k in data["mapStats"]: del data["mapStats"][k]
            if "actors_data" in data and prefix == "Giant":
                 data["actors_data"] = [x for x in data["actors_data"] if (x.get("favorite") or x.get("kills", 0) > 0)]

        base_name = f"{prefix}_Save{slot_num}.json"
        final_path = os.path.join(self.downloads_path, base_name)
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=None, ensure_ascii=False)
        return final_path

    # === ТВОЙ ОРИГИНАЛЬНЫЙ ПАРСЕР ===
    def apply_exact_algorithm(self, data, slot_num, mode_idx):
        # mode_idx: 3=Classic, 4=Mini, 5=Ultra
        
        LIMIT_LISTS = 1000000
        PROCESS_CITY_RES = True
        PROCESS_STATS_ALL = True
        
        if mode_idx == 4: # Mini
            LIMIT_LISTS = 15
            PROCESS_CITY_RES = False
            PROCESS_STATS_ALL = False
        elif mode_idx == 5: # Ultra
            LIMIT_LISTS = 3
            PROCESS_CITY_RES = False
            PROCESS_STATS_ALL = False
            
        TIME_DIVIDER = 60.0
        txt_unknown = self.get_text("unknown")
        txt_nature = self.get_text("nature")
        
        max_tick = 0
        if "mapStats" in data: max_tick = max(max_tick, data["mapStats"].get("worldTime", 0))
        true_year = int(max_tick // TIME_DIVIDER)

        mode_name = self.get_text("modes")[mode_idx]
        final_report = {
            "CONTEXT": {"True_Year": true_year, "Era": data.get("mapStats", {}).get("era_id", txt_unknown), "Mode": mode_name},
            "HISTORY": {"Wars": [], "Alliances": [], "Plots": []},
            "SOCIETY": {"Languages": [], "Religions": [], "Cultures": [], "Clans": [], "Books": data.get("books", [])},
            "POLITICS": {"Kingdoms": [], "Relations": data.get("relations", []), "Subspecies": []},
            "ECONOMY_CITIES": [], "VIP_PEOPLE": [], "WORLD_RECORDS": {}
        }

        # LIST FILTERS
        def get_sorted(key, sort_key):
            if key in data: return sorted(data[key], key=lambda x: x.get(sort_key, 0), reverse=True)[:LIMIT_LISTS]
            return []

        final_report["SOCIETY"]["Languages"] = get_sorted("languages", "speakers_new")
        final_report["HISTORY"]["Plots"] = get_sorted("plots", "created_time")
        if "alliances" in data: final_report["HISTORY"]["Alliances"] = data["alliances"]
        
        for c in get_sorted("cultures", "renown"):
            final_report["SOCIETY"]["Cultures"].append({
                "Name": c.get("name"), "Renown": c.get("renown"), "Techs": len(c.get("list_tech_ids", [])),
                "Total_Kills": c.get("total_kills"), "Founded": int(c.get("created_time", 0) // TIME_DIVIDER)
            })
        for cl in get_sorted("clans", "units_count"):
            c_copy = cl.copy()
            if "units" in c_copy: del c_copy["units"]
            final_report["SOCIETY"]["Clans"].append(c_copy)
        for r in get_sorted("religions", "followers"):
            final_report["SOCIETY"]["Religions"].append({
                "Name": r.get("name"), "Followers": r.get("followers"), "Founded": int(r.get("created_time", 0) // TIME_DIVIDER)
            })
        if "subspecies" in data:
            for s in sorted(data["subspecies"], key=lambda x: (x.get("total_kills", 0) + x.get("total_deaths", 0)), reverse=True)[:LIMIT_LISTS]:
                final_report["POLITICS"]["Subspecies"].append({
                    "Name": s.get("name"), "Race": s.get("species_id"), "Traits": s.get("saved_traits", []),
                    "Kills": s.get("total_kills"), "Deaths": s.get("total_deaths")
                })

        # MATH
        actors = data.get("actors_data", [])
        city_pop, city_mil, k_pop, k_mil, k_armies = {}, {}, {}, {}, {}
        for a in actors:
            cid = a.get("cityID"); kid = a.get("civ_kingdom_id")
            army = a.get("army") is not None
            if cid:
                city_pop[cid] = city_pop.get(cid, 0) + 1
                if army: city_mil[cid] = city_mil.get(cid, 0) + 1
            if kid:
                k_pop[kid] = k_pop.get(kid, 0) + 1
                if army: k_mil[kid] = k_mil.get(kid, 0) + 1
        for ar in data.get("armies", []):
            kid = ar.get("id_kingdom")
            if kid: k_armies[kid] = k_armies.get(kid, 0) + 1

        item_stats = {}
        if mode_idx != 5:
            for item in data.get("items", []):
                kn = item.get("from", txt_unknown)
                if kn not in item_stats: item_stats[kn] = {}
                iid = item.get("asset_id")
                if iid: item_stats[kn][iid] = item_stats[kn].get(iid, 0) + 1

        city_resources = {}
        buildings = data.get("buildings", [])
        def extract(obj, cid):
            if not cid or not obj: return
            if cid not in city_resources: city_resources[cid] = {}
            for k in ["resources", "storage", "inventory", "equipment"]:
                cont = obj.get(k)
                if not cont: continue
                raw = []
                if isinstance(cont, dict):
                    raw = cont.get("saved_resources") or cont.get("resources") or cont.get("items") or []
                    if not raw and not isinstance(raw, list):
                        for rid, v in cont.items():
                            if isinstance(v, (int, float)): city_resources[cid][rid] = city_resources[cid].get(rid, 0) + v
                elif isinstance(cont, list): raw = cont
                if isinstance(raw, list):
                    for it in raw:
                        if isinstance(it, dict):
                            rid = it.get("id") or it.get("asset_id")
                            amt = it.get("amount", 1)
                            if rid: city_resources[cid][rid] = city_resources[cid].get(rid, 0) + amt
        
        if "cities" in data:
            for c in data["cities"]: extract(c, c.get("id"))
        for b in buildings: extract(b, b.get("cityID") or b.get("city_id"))

        vip_ids = set()
        food_items = ["wheat", "bread", "meat", "fish", "sushi", "jam", "cider", "pie", "tea", "soup", "berries", "ale", "burger", "coconut", "mushrooms", "herbs", "worms", "banana", "cactus", "candy", "lemon"]

        # CITIES
        if "cities" in data and mode_idx != 5:
            for c in data["cities"]:
                if c.get("leaderID"): vip_ids.add(str(c.get("leaderID")))
                cid = c.get("id")
                res = city_resources.get(cid, {})
                entry = {
                    "Name": c.get("name"), "ID": cid, "Kingdom_ID": c.get("kingdomID"),
                    "Race": c.get("original_actor_asset"), "Pop": city_pop.get(cid, 0),
                    "Gold": res.get("gold", 0), "Food": sum(res.get(x, 0) for x in food_items),
                    "Founded": int(c.get("created_time", 0) // TIME_DIVIDER)
                }
                if PROCESS_CITY_RES:
                    entry["Full_Resources"] = dict(sorted(res.items(), key=lambda x: x[1], reverse=True)[:10])
                final_report["ECONOMY_CITIES"].append(entry)

        # KINGDOMS
        k_cities_map = {}
        if "cities" in data:
            for c in data["cities"]:
                kid = c.get("kingdomID") or c.get("last_kingdom_id")
                if kid: k_cities_map.setdefault(kid, []).append(c.get("id"))
        if "kingdoms" in data:
            for k in data["kingdoms"]:
                if k.get("hidden"): continue
                if k.get("kingID"): vip_ids.add(str(k.get("kingID")))
                kid = k.get("id")
                kg = 0; kf = 0
                for cid in k_cities_map.get(kid, []):
                    r = city_resources.get(cid, {})
                    kg += r.get("gold", 0); kf += sum(r.get(x, 0) for x in food_items)
                
                ks = {
                    "Name": k.get("name"), "ID": kid, "Race": k.get("original_actor_asset"),
                    "Pop": k_pop.get(kid, 0), "Mil": k_mil.get(kid, 0), "King": k.get("kingID"),
                    "Gold": kg, "Food": kf, "Renown": k.get("renown"), "Kills": k.get("total_kills"),
                    "Founded": int(k.get("created_time", 0) // TIME_DIVIDER)
                }
                if mode_idx != 5:
                    kw = item_stats.get(k.get("name"), {})
                    ks["Weapons"] = dict(sorted(kw.items(), key=lambda x: x[1], reverse=True)[:5])
                final_report["POLITICS"]["Kingdoms"].append(ks)

        # WARS
        if "wars" in data:
            target_wars = data["wars"]
            if mode_idx == 4: # Mini
                sorted_w = sorted(data["wars"], key=lambda x: x.get("total_deaths", 0), reverse=True)
                target_wars = sorted_w[:LIMIT_LISTS]
            elif mode_idx == 5: # Ultra
                target_wars = [w for w in data["wars"] if not w.get("ended", True)]
            
            for w in target_wars:
                final_report["HISTORY"]["Wars"].append({
                    "Attacker": w.get("main_attacker"), "Defender": w.get("main_defender"),
                    "Type": w.get("war_type"), "Deaths": w.get("total_deaths", "Unknown"),
                    "Start": int(w.get("created_time", 0) // TIME_DIVIDER)
                })

        # VIP & STATS
        records_data = {}
        TRAIT_STATS = {
            "genius": {"intelligence": 10, "warfare": 5, "diplomacy": 5, "stewardship": 7},
            "stupid": {"intelligence": -5, "warfare": -2, "diplomacy": -2, "stewardship": -5},
            "wise": {"intelligence": 1, "warfare": 1, "diplomacy": 1, "stewardship": 1},
            "ambitious": {"diplomacy": 2, "warfare": 4, "stewardship": 1, "intelligence": 0},
            "content": {"diplomacy": 2, "stewardship": 2, "warfare": -2},
            "greedy": {"diplomacy": -2, "warfare": 4, "stewardship": -3},
            "honest": {"diplomacy": 2, "stewardship": 3, "warfare": -2},
            "deceitful": {"diplomacy": 1, "stewardship": 4},
            "pacifist": {"diplomacy": 10, "warfare": -4},
            "bloodlust": {"diplomacy": -2, "warfare": 10},
            "paranoid": {"diplomacy": -2, "warfare": 4, "stewardship": 0},
            "strong": {"warfare": 2},
            "weak": {"warfare": -2, "diplomacy": -2},
            "tough": {"warfare": 1},
            "pyromaniac": {"warfare": 3},
            "veteran": {"warfare": 5},
            "kingslayer": {"warfare": 5, "diplomacy": -5},
            "mageslayer": {"warfare": 5},
            "dragonslayer": {"warfare": 6, "diplomacy": 2},
            "golden_tooth": {"diplomacy": 2},
            "evil": {"warfare": 10},
            "blessed": {"diplomacy": 5, "warfare": 5, "stewardship": 5, "intelligence": 5},
            "cursed": {"diplomacy": -10, "warfare": -5, "stewardship": -5},
            "madness": {"diplomacy": -100},
            "attractive": {"diplomacy": 2, "stewardship": 1},
            "ugly": {"diplomacy": -2},
            "lustful": {"diplomacy": -2},
            "voices_in_my_head": {"diplomacy": -1},
            "crippled": {"diplomacy": -3},
            "eyepatch": {"diplomacy": 1, "warfare": -1},
            "skin_burns": {"diplomacy": -2, "warfare": 2},
            "moonchild": {"intelligence": 3},
            "nightchild": {"warfare": 3},
            "strong_minded": {"intelligence": 2},
            "savage": {"warfare": 3, "intelligence": -2}
        }
        
        sub_trait_map = {}
        if "subspecies" in data:
            for s in data["subspecies"]: sub_trait_map[s.get("id")] = s.get("saved_traits", [])
        
        items_map = {str(i.get("id")): i for i in data.get("items", [])}
        
        for actor in actors:
            aid = str(actor.get("id"))
            fav = actor.get("favorite", False)
            
            is_vip = (aid in vip_ids) or fav
            if not is_vip and not PROCESS_STATS_ALL: continue 
            
            a_traits = actor.get("saved_traits", []) or []
            c_floats = actor.get("custom_data_float", {})
            c_ints = actor.get("custom_data_int", {})
            
            def calculate_final_stat(stat_key, base=4.0):
                val = c_floats.get(stat_key)
                if val is None: val = c_ints.get(stat_key)
                if val is None: val = actor.get(stat_key)
                if val is None: val = 0.0
                try: total = float(val) + base
                except: total = base
                for trait in a_traits:
                    if trait in TRAIT_STATS: total += TRAIT_STATS[trait].get(stat_key, 0)
                sub_traits = sub_trait_map.get(actor.get("subspecies"), [])
                for st in sub_traits:
                    if st in TRAIT_STATS: total += TRAIT_STATS[st].get(stat_key, 0)
                return round(total, 1)

            s_intel = calculate_final_stat("intelligence")
            s_stew = calculate_final_stat("stewardship")
            s_war = calculate_final_stat("warfare")
            s_dipl = calculate_final_stat("diplomacy")
            
            age = float(actor.get("age_overgrowth") or 0)
            hp = float(actor.get("health") or 0)
            kills = float(actor.get("kills") or 0)
            
            if mode_idx != 5:
                curr = {"Age": age, "Kills": kills, "Health": hp, "Int": s_intel, "War": s_war}
                for cat, val in curr.items():
                    mx = f"{cat}_max"
                    if mx not in records_data or val > records_data[mx]["v"]:
                        records_data[mx] = {"v": val, "actor": actor, "stats": curr}

            if is_vip:
                person = {
                    "Name": actor.get("name"), "ID": aid, "Fav": fav,
                    "Age": age, "Kills": kills, "Traits": a_traits,
                    "Stats": {"Int": s_intel, "Stew": s_stew, "War": s_war, "Dipl": s_dipl}
                }
                if mode_idx == 3: # Classic
                    arts = []
                    for itid in actor.get("saved_items", []):
                        it = items_map.get(str(itid))
                        if it: arts.append(it.get("name") or it.get("asset_id"))
                    person["Artifacts"] = arts
                final_report["VIP_PEOPLE"].append(person)

        txt_rec = self.get_text("record")
        for k, win in records_data.items():
            act = win["actor"]
            if not act: continue
            lbl = k.replace("_max", txt_rec)
            final_report["WORLD_RECORDS"][lbl] = {
                "Winner": act.get("name") or txt_unknown, "Val": win["v"],
                "Traits": act.get("saved_traits", [])
            }

        # SAVE
        mode_tags = ["Custom", "Iceberg", "Giant", "Classic", "Mini", "Ultra"]
        base_name = f"Ideal_WB_{mode_tags[mode_idx]}_Save{slot_num}.txt"
        final_path = os.path.join(self.downloads_path, base_name)
        with open(final_path, 'w', encoding='utf-8') as f: json.dump(final_report, f, indent=1, ensure_ascii=False)
        return final_path

if __name__ == "__main__":
    app = WorldBoxFinalApp()
    app.mainloop()