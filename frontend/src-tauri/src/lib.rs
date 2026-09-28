use tauri::{AppHandle, Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::ShellExt;
use std::sync::Mutex;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

#[tauri::command]
fn wait_for_backend() -> Result<String, String> {
    let client = reqwest::blocking::Client::new();
    let mut attempts = 0;
    while attempts < 30 {
        if let Ok(res) = client.get("http://127.0.0.1:8000/health").send() {
            if res.status().is_success() {
                return Ok("Backend ready".to_string());
            }
        }
        std::thread::sleep(std::time::Duration::from_millis(500));
        attempts += 1;
    }
    Err("Backend timeout".to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_log::Builder::default().level(log::LevelFilter::Info).build())
        .invoke_handler(tauri::generate_handler![wait_for_backend])
        .setup(|app| {
            let sidecar_command = app.shell().sidecar("kshaya-backend")
                .expect("failed to create sidecar configuration");
            
            let (mut rx, child) = sidecar_command
                .spawn()
                .expect("failed to spawn sidecar");
            
            app.manage(BackendProcess(Mutex::new(Some(child))));
            
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    println!("Sidecar event: {:?}", event);
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::ExitRequested { .. } | RunEvent::WindowEvent { event: WindowEvent::CloseRequested { .. }, .. } = event {
                let state: tauri::State<BackendProcess> = app_handle.state();
                if let Some(child) = state.0.lock().unwrap().take() {
                    println!("Terminating backend sidecar...");
                    let _ = child.kill();
                }
            }
        });
}
