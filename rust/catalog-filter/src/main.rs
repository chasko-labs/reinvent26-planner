//! catalog-filter: read a json array of sessions on stdin, write matches on stdout.
//! usage: catalog-filter --topics agents,mcp --levels 300,400 [--day 2026-12-01]
//! zero third-party deps: string-level json scan keeps the helper dependency-free.

use std::env;
use std::io::Read;

fn arg_value(name: &str) -> Option<String> {
    let args: Vec<String> = env::args().collect();
    args.windows(2).find(|w| w[0] == name).map(|w| w[1].clone())
}

fn split_lower(v: Option<String>) -> Vec<String> {
    v.unwrap_or_default()
        .split(',')
        .map(|s| s.trim().to_lowercase())
        .filter(|s| !s.is_empty())
        .collect()
}

// minimal object splitter: tracks brace depth outside strings.
fn split_objects(raw: &str) -> Vec<&str> {
    let bytes = raw.as_bytes();
    let mut out = Vec::new();
    let mut depth = 0;
    let mut in_str = false;
    let mut esc = false;
    let mut start: Option<usize> = None;
    let mut i = 0;
    while i < bytes.len() {
        let c = bytes[i] as char;
        if in_str {
            if esc {
                esc = false;
            } else if c == '\\' {
                esc = true;
            } else if c == '"' {
                in_str = false;
            }
        } else if c == '"' {
            in_str = true;
        } else if c == '{' {
            if depth == 0 {
                start = Some(i);
            }
            depth += 1;
        } else if c == '}' {
            if depth > 0 {
                depth -= 1;
            }
            if depth == 0 {
                if let Some(s) = start.take() {
                    out.push(&raw[s..=i]);
                }
            }
        }
        i += 1;
    }
    out
}

// Match a level filter against the "level" field value when present, so a
// filter like 300 does not match a startTime that merely contains "300".
// Falls back to a whole-object substring match when no "level" key exists.
fn level_matches(low_obj: &str, level: &str) -> bool {
    let mut found_key = false;
    let mut search = low_obj;
    while let Some(idx) = search.find("\"level\"") {
        found_key = true;
        let window = &search[idx..search.len().min(idx + 48)];
        if window.contains(level) {
            return true;
        }
        search = &search[idx + 7..];
    }
    if found_key {
        return false;
    }
    low_obj.contains(level)
}

fn main() {
    let topics = split_lower(arg_value("--topics"));
    let levels = split_lower(arg_value("--levels"));
    let day = arg_value("--day").unwrap_or_default();

    let mut raw = String::new();
    std::io::stdin().read_to_string(&mut raw).unwrap_or(0);

    let mut hits: Vec<&str> = Vec::new();
    for obj in split_objects(&raw) {
        let low = obj.to_lowercase();
        if !topics.is_empty() && !topics.iter().any(|t| low.contains(t)) {
            continue;
        }
        if !levels.is_empty() && !levels.iter().any(|l| level_matches(&low, l)) {
            continue;
        }
        if !day.is_empty() && !low.contains(&day.to_lowercase()) {
            continue;
        }
        hits.push(obj);
    }

    print!("[{}]", hits.join(","));
}

#[cfg(test)]
mod tests {
    use super::{level_matches, split_objects};

    #[test]
    fn splits_two_objects() {
        let raw = r#"[{"a":1},{"a":2}]"#;
        assert_eq!(split_objects(raw).len(), 2);
    }

    #[test]
    fn level_filter_ignores_timestamps() {
        let obj = r#"{"sessionId":"a","level":"200","startTime":"2026-12-01T13:00:00"}"#;
        assert!(!level_matches(&obj.to_lowercase(), "300"));
        assert!(level_matches(&obj.to_lowercase(), "200"));
    }

    #[test]
    fn level_filter_falls_back_without_key() {
        assert!(level_matches("plain 300 text", "300"));
    }
}
