use tauri::Manager;
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};
use std::thread;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        let _ = app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        );
      }

      // 1. Resolve backend path based on dev/release mode
      let mut cmd = if cfg!(debug_assertions) {
        // Dev: Spawn using virtual environment python against server_app.py
        let mut c = Command::new("../../.venv/Scripts/python.exe");
        c.arg("../../server_app.py");
        c
      } else {
        // Release: Resolve sidecar path relative to current executable
        let exe_path = std::env::current_exe().unwrap();
        let exe_dir = exe_path.parent().unwrap();
        let mut sidecar = exe_dir.join("server-sidecar.exe");
        if !sidecar.exists() {
          sidecar = exe_dir.join("resources").join("server-sidecar-x86_64-pc-windows-msvc.exe");
        }
        Command::new(sidecar)
      };

      // Inject resources dir into PATH so backend sidecar can find bundled ffmpeg and ffprobe
      if let Ok(resource_dir) = app.path().resource_dir() {
        if let Ok(current_path) = std::env::var("PATH") {
          let separator = if cfg!(windows) { ";" } else { ":" };
          let new_path = format!("{}{}{}", resource_dir.to_string_lossy(), separator, current_path);
          cmd.env("PATH", new_path);
        }
      }

      cmd.stdout(Stdio::piped());
      cmd.stderr(Stdio::piped());

      // 2. Spawn backend and read stdout in a separate thread
      let mut child = cmd.spawn().expect("failed to spawn backend process");
      let stdout = child.stdout.take().unwrap();
      let reader = BufReader::new(stdout);
      
      let app_handle = app.handle().clone();

      thread::spawn(move || {
        for line in reader.lines() {
          if let Ok(line_str) = line {
            println!("[Backend] {}", line_str);
            
            // 3. Intercept secure startup token
            if line_str.starts_with("BAYNUMAN_TOKEN:") {
              let token = line_str.trim_start_matches("BAYNUMAN_TOKEN:").to_string();
              println!("[Tauri] Intercepted backend token: {}", token);
              
              // 4. Inject token query param, navigate main window, and reveal
              let app_handle_clone = app_handle.clone();
              let _ = app_handle.run_on_main_thread(move || {
                if let Some(window) = app_handle_clone.get_webview_window("main") {
                  if let Ok(mut url) = window.url() {
                    url.set_query(Some(&format!("token={}", token)));
                    let _ = window.navigate(url);
                    let _ = window.show();
                  }
                }
              });
            }
          }
        }
        let _ = child.wait();
      });

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
