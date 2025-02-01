import sys
from pathlib import Path
from src.Utils import sav, utils
from win32gui import FindWindow, SetForegroundWindow

PARENT_PATH = Path(__file__).parent
ASSETS_PATH = PARENT_PATH / Path(r"src/assets")
LOG         = utils.LOGGER()
config_file = PARENT_PATH / Path("tenebris.json")
this_window = FindWindow(None, "FSSE - Fallout Shelter Save Editor")

if this_window != 0:
    LOG.warning("FSSE is aleady running! Only one instance can be launched at once.\n")
    SetForegroundWindow(this_window)
    sys.exit(0)
LOG.OnStart(PARENT_PATH)

if getattr(sys, 'frozen', False):
    import pyi_splash


def res_path(path: str) -> Path:
    return ASSETS_PATH / Path(path)


import asyncio
import atexit
import imgui
import os
from src.GUI import gui
from threading import Thread
from imgui.integrations.glfw import GlfwRenderer

Icons = gui.Icons
task_status = "Idle."
loop = asyncio.new_event_loop()
Thread(target = loop.run_forever, daemon = True).start()


async def update_status(new_status, reset_after = 2):
    global task_status
    task_status = new_status
    await asyncio.sleep(reset_after)
    task_status = "Idle."


def update_task(new_status):
    asyncio.run_coroutine_threadsafe(update_status(new_status, 2), loop)


def OnDraw():
    file_selected = False
    save_data     = None
    dweller_index = 0
    dweller_names = []
    game_modes    = ["Normal", "Survival"]
    imgui.create_context()
    window, text_cursor = gui.new_window("FSSE - Fallout Shelter Save Editor", 300, 300)
    impl = GlfwRenderer(window)
    font_scaling_factor = gui.fb_to_window_factor(window)
    io = imgui.get_io()
    io.fonts.clear()
    io.font_global_scale = 1.0 / font_scaling_factor
    font_config = imgui.core.FontConfig(merge_mode = True)
    icons_range = imgui.core.GlyphRanges([0xF000, 0xF21E, 0])

    title_font = io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/Rokkitt-Regular.ttf")), 25 * font_scaling_factor,
    )
    
    subtitle_font = io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/Rokkitt-Regular.ttf")), 22.5 * font_scaling_factor,
    )

    main_font = io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/Rokkitt-Regular.ttf")), 20 * font_scaling_factor,
    )

    io.fonts.add_font_from_file_ttf(
        str(res_path("fonts/fontawesome-webfont.ttf")), 16 * font_scaling_factor,
        font_config, icons_range
    )

    impl.refresh_font_texture()
    

    while not gui.glfw.window_should_close(window):
        gui.glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()

        win_w, win_h = gui.glfw.get_window_size(window)
        imgui.set_next_window_size(win_w, win_h)
        imgui.set_next_window_position(0, 0)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, 0.08, 0.08, 0.08)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_ACTIVE, 0.2, 0.2, 0.2)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_HOVERED, 0.3, 0.3, 0.3)
        imgui.push_style_color(imgui.COLOR_HEADER, 0.1, 0.1, 0.1)
        imgui.push_style_color(imgui.COLOR_HEADER_ACTIVE, 0.2, 0.2, 0.2)
        imgui.push_style_color(imgui.COLOR_HEADER_HOVERED, 0.3, 0.3, 0.3)
        imgui.push_style_color(imgui.COLOR_BUTTON, 0.08, 0.08, 0.08)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.2, 0.2, 0.2)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.3, 0.3, 0.3)
        imgui.push_style_var(imgui.STYLE_CHILD_ROUNDING, 10)
        imgui.push_style_var(imgui.STYLE_FRAME_ROUNDING, 10)
        imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (10, 10))
        imgui.push_style_var(imgui.STYLE_ITEM_INNER_SPACING, (10, 10))
        imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (10, 10))
        imgui.begin("Main Window", flags =
                    imgui.WINDOW_NO_TITLE_BAR |
                    imgui.WINDOW_NO_RESIZE |
                    imgui.WINDOW_NO_MOVE
                    )
        imgui.push_font(main_font)
        imgui.push_text_wrap_pos(win_w - 5)
        
        if not file_selected:
            text_size = imgui.calc_text_size(f"{Icons.Folder}  Select Save File")
            imgui.dummy(1, (win_h / 2) - 40)
            imgui.dummy((win_w / 2) - (text_size.x / 1.3), 1)
            imgui.same_line()
            if imgui.button(f"{Icons.Folder}  Select Save File"):
                sav_file = gui.start_file_dialog("SAV\0*.sav", multiselect = False)
                if sav_file is not None:
                    if os.path.isfile(sav_file) and sav_file.endswith(".sav"):
                        LOG.info(f"Found valid save file at {sav_file}")
                        file_selected = True
                        LOG.info("Decrypting save file...")
                        save_data = sav.read_save_file(sav_file)
                        gui.set_window_size(window, 600, 500)
                        if save_data is not None:
                            LOG.info("Save data converted to JSON, reading information...")
                            LOG.info(f"Found game version {save_data["appVersion"]}")
                            LOG.info(f"Finished reading save information for vault {save_data["vault"]["VaultName"]}")
        else:
            if save_data is not None:
                vault              = save_data["vault"]
                game_version       = save_data["appVersion"]
                dwellers           = save_data["dwellers"]["dwellers"]
                # pets_and_actors    = save_data["dwellers"]["actors"]
                vault_number       = vault["VaultName"]
                gameplay_mode      = vault["VaultMode"]
                lunchboxesByType   = vault["LunchBoxesByType"]
                storage            = vault["storage"]["resources"]
                caps               = int(storage["Nuka"])
                food               = int(storage["Food"])
                energy             = int(storage["Energy"])
                water              = int(storage["Water"])
                stimPacks          = int(storage["StimPack"])
                radAway            = int(storage["RadAway"])
                nuka               = int(storage["NukaColaQuantum"])
                all_lunchbox_count = len(lunchboxesByType)
                lunchboxes_count   = sav.get_lunchbox_count(lunchboxesByType, 0)
                mr_handies_count   = sav.get_lunchbox_count(lunchboxesByType, 1)
                pet_carrier_count  = sav.get_lunchbox_count(lunchboxesByType, 2)
                starter_pack_count = sav.get_lunchbox_count(lunchboxesByType, 3)

                with imgui.font(title_font):
                    imgui.text(f"Vault: {vault_number}"); imgui.same_line()
                    imgui.text(f"|  Game Mode: {gameplay_mode}"); imgui.same_line()
                    imgui.text(f"|  Game Version: {game_version}")

                imgui.begin_child("Main", 0, -120, border = True)
                if imgui.begin_tab_bar("main"):
                    if imgui.begin_tab_item("Vault").selected:
                        game_mode_index = 0 if gameplay_mode == "Normal" else 1
                        imgui.text("Name:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 6)
                        imgui.set_next_item_width(50)
                        entered, vault_number, = imgui.input_text(
                            "##vaultName", vault_number, 3,
                            imgui.INPUT_TEXT_CHARS_DECIMAL | imgui.INPUT_TEXT_CHARS_NO_BLANK
                        )
                        if imgui.is_item_hovered():
                            gui.set_text_cursor(window, text_cursor)
                        elif not imgui.is_any_item_hovered():
                            gui.set_text_cursor(window, None)

                        if entered:
                            if len(vault_number) == 3:
                                vault["VaultName"] = vault_number
                        
                        imgui.text("Game Mode: ")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 14.5)
                        imgui.set_next_item_width(120)
                        mode_changed, game_mode_index = imgui.combo("##gameMode", game_mode_index, game_modes)
                        if mode_changed:
                            vault["VaultMode"] = game_modes[game_mode_index]

                        imgui.end_tab_item()
                    if imgui.begin_tab_item("Lunchboxes").selected:
                        with imgui.font(subtitle_font):
                            imgui.text(f"Total Boxes: [ {all_lunchbox_count} ]")
                        imgui.separator(); imgui.text(f"{Icons.Box}  Lunch Boxes:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 10)
                        imgui.push_item_width(200)
                        lb_changed, lunchboxes_count = imgui.input_int("##lunchboxes", lunchboxes_count, 1, 1)
                        if lb_changed:
                            sav.update_lunchbox_count(vault, 0, lunchboxes_count)
                        
                        imgui.text(f"{Icons.Droid}  Mr Handy:")
                        imgui.same_line(spacing = content_region / 7.2)
                        mh_changed, mr_handies_count = imgui.input_int("##mrHandy", mr_handies_count, 1, 1)
                        if mh_changed:
                            sav.update_lunchbox_count(vault, 1, mr_handies_count)
                        
                        imgui.text(f"{Icons.Paw}  Pet Carrier:")
                        imgui.same_line(spacing = content_region / 8.3)
                        pc_changed, pet_carrier_count = imgui.input_int("##petCarrier", pet_carrier_count, 1, 1)
                        if pc_changed:
                            sav.update_lunchbox_count(vault, 2, pet_carrier_count)

                        imgui.text(f"{Icons.Gift}  Starter Pack:")
                        imgui.same_line(spacing = content_region / 9.2)
                        sp_changed, starter_pack_count = imgui.input_int("##starterPack", starter_pack_count, 1, 1)
                        if sp_changed:
                            sav.update_lunchbox_count(vault, 3, starter_pack_count)

                        imgui.pop_item_width()
                        imgui.end_tab_item()
                    
                    if imgui.begin_tab_item("Resources").selected:
                        imgui.push_item_width(200)
                        imgui.text(f"{Icons.Money}  Caps:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 5.3)
                        caps_changed, caps = imgui.input_int("##caps", caps, 1, 1)
                        if caps_changed:
                            storage["Nuka"] = caps

                        imgui.text(f"{Icons.Money}  NukaCola:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 8)
                        imgui.push_item_width(200)
                        nuka_changed, nuka = imgui.input_int("##nukacola", nuka, 1, 1)
                        if nuka_changed:
                            storage["NukaColaQuantum"] = nuka
                        
                        imgui.text(f"{Icons.Food}   Food:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 5.3)
                        food_changed, food = imgui.input_int("##food", food, 1, 1)
                        if food_changed:
                            storage["Food"] = food
                        
                        imgui.text(f"{Icons.Flash}  Energy:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 5.8)
                        energy_changed, energy = imgui.input_int("##energy", energy, 1, 1)
                        if energy_changed:
                            storage["Energy"] = energy
                        
                        imgui.text(f"{Icons.Glass}  Water:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 5.7)
                        water_changed, water = imgui.input_int("##water", water, 1, 1)
                        if water_changed:
                            storage["Water"] = water
                        
                        imgui.text(f"{Icons.Medkit}  StimPacks:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 8.5)
                        stimpacks_changed, stimPacks = imgui.input_int("##stimpack", stimPacks, 1, 1)
                        if stimpacks_changed:
                            storage["StimPack"] = stimPacks
                        
                        imgui.text(f"{Icons.Heartbeat}  RadAway:")
                        content_region = imgui.get_content_region_available_width()
                        imgui.same_line(spacing = content_region / 7.9)
                        ardaway_changed, radAway = imgui.input_int("##radaway", radAway, 1, 1)
                        if ardaway_changed:
                            storage["RadAway"] = radAway

                        imgui.pop_item_width()
                        imgui.end_tab_item()

                    if imgui.begin_tab_item("Dwellers").selected:
                        if len(dwellers) > 0:
                            dweller_names = sav.get_dweller_names(dwellers)
                            total_dwellers = len(dweller_names)
                            with imgui.font(subtitle_font):
                                imgui.text(f"Total Dwellers: [ {total_dwellers} ]")

                            imgui.dummy((win_w / 2) - 200, 1)
                            imgui.same_line()
                            imgui.set_next_item_width(300)
                            _, dweller_index = imgui.combo("##dwellers", dweller_index, dweller_names)
                            gender     = dwellers[dweller_index]["gender"] == 2 and "Male" or "Female"
                            happiness  = int(dwellers[dweller_index]["happiness"]["happinessValue"])
                            health     = int(dwellers[dweller_index]["health"]["healthValue"])
                            radiation  = int(dwellers[dweller_index]["health"]["radiationValue"])
                            permadeath = bool(dwellers[dweller_index]["health"]["permaDeath"])
                            total_xp   = int(dwellers[dweller_index]["experience"]["experienceValue"])
                            curr_level = int(dwellers[dweller_index]["experience"]["currentLevel"])
                            imgui.dummy(1, 10)
                            imgui.push_item_width(200)

                            imgui.text(f"Gender:        {gender}")
                            imgui.text(f"Health:          {health}")
                            if health < 100:
                                content_region = imgui.get_content_region_available_width()
                                imgui.same_line(spacing = content_region / 10)
                                if imgui.button("Heal"):
                                    dwellers[dweller_index]["health"]["healthValue"] = 100

                            imgui.text(f"Radiation:    {radiation}")
                            if radiation > 0:
                                content_region = imgui.get_content_region_available_width()
                                imgui.same_line(spacing = content_region / 10)
                                if imgui.button("Remove Radiation"):
                                    dwellers[dweller_index]["health"]["radiationValue"] = 0

                            imgui.text("Happiness: ")
                            content_region = imgui.get_content_region_available_width()
                            imgui.same_line(spacing = content_region / 6)
                            happiness_changed, happiness = imgui.slider_int("##happiness", happiness, 10, 100)
                            if happiness_changed:
                                dwellers[dweller_index]["happiness"]["happinessValue"] = happiness

                            imgui.text("Experience Points: ")
                            content_region = imgui.get_content_region_available_width()
                            imgui.same_line(spacing = content_region / 15)
                            xp_changed, total_xp = imgui.input_int("##xp", total_xp, 1, 1)
                            if xp_changed:
                                dwellers[dweller_index]["experience"]["experienceValue"] = total_xp

                            imgui.text("Level: ")
                            content_region = imgui.get_content_region_available_width()
                            imgui.same_line(spacing = content_region / 4.2)
                            lvl_changed, curr_level = imgui.input_int("##lvl", curr_level, 1, 1)
                            if lvl_changed:
                                dwellers[dweller_index]["experience"]["currentLevel"] = curr_level
                            
                            imgui.text("Perma Death: ")
                            content_region = imgui.get_content_region_available_width()
                            imgui.same_line(spacing = content_region / 7)
                            checked, permadeath = imgui.checkbox(permadeath and "On" or "Off", permadeath)
                            if checked:
                                dwellers[dweller_index]["health"]["permaDeath"] = permadeath

                            imgui.pop_item_width()
                        else:
                            imgui.text("Vault has no dwellers.")
                        imgui.end_tab_item()
                    imgui.end_tab_bar()
                imgui.end_child()

            imgui.dummy(1, 5)
            if imgui.button(f"{Icons.Save}  Save Changes"):
                try:
                    update_task(f"{Icons.Spinner}  Writing data to {os.path.basename(sav_file)}")
                    LOG.info(f"Writing data to {sav_file}")
                    sav.write_save_file(sav_file, save_data)
                    LOG.info("Done.")
                except Exception as e:
                    LOG.error(f"Failed to write data: {e}")
                    update_task("Failed to write data!")
                    pass
            
            imgui.same_line()
            if imgui.button(f"{Icons.Close}  Return To Main Menu"):
                file_selected = False
                save_data = None
                gui.set_window_size(window, 300, 300)

            imgui.same_line()
            if imgui.button(f"{Icons.File_c}  Export To JSON"):
                try:
                    LOG.info("Exporting save data to JSON...")
                    update_task(f"{Icons.Spinner}  Exporting save data to JSON...")
                    sav.save_to_json(save_data, sav_file)
                    LOG.info("Done.")
                except Exception as e:
                    LOG.error(f"Failed to export data to JSON: {e}")
                    update_task("Failed to export data!")
                    pass
            
            imgui.separator(); imgui.text(f"Status: {task_status}")

        imgui.pop_font()
        imgui.pop_text_wrap_pos()
        imgui.pop_style_color(9)
        imgui.pop_style_var(5)
        imgui.end()

        gui.gl.glClearColor(1.0, 1.0, 1.0, 1)
        gui.gl.glClear(gui.gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        gui.glfw.swap_buffers(window)

    impl.shutdown()
    gui.glfw.terminate()

@atexit.register
def OnExit():
    LOG.info("Closing application...\n\nFarewell!")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        pyi_splash.close()
    OnDraw()