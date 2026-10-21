// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

/// Decodes a base64 encoded string into raw bytes without requiring external crate dependencies.
pub fn decode_base64(input: &str) -> Result<Vec<u8>, String> {
    let clean_input = if let Some(idx) = input.find(',') {
        &input[idx + 1..]
    } else {
        input
    };

    let chars: Vec<char> = clean_input.chars().filter(|c| !c.is_whitespace()).collect();
    let mut buffer: Vec<u8> = Vec::new();
    let mut i = 0;

    fn b64_val(c: char) -> Result<u32, String> {
        match c {
            'A'..='Z' => Ok(c as u32 - 'A' as u32),
            'a'..='z' => Ok(c as u32 - 'a' as u32 + 26),
            '0'..='9' => Ok(c as u32 - '0' as u32 + 52),
            '+' => Ok(62),
            '/' => Ok(63),
            '=' => Ok(0),
            _ => Err(format!("Invalid base64 character: {}", c)),
        }
    }

    while i < chars.len() {
        if i + 3 >= chars.len() {
            break;
        }
        let c1 = chars[i];
        let c2 = chars[i + 1];
        let c3 = chars[i + 2];
        let c4 = chars[i + 3];

        let n1 = b64_val(c1)?;
        let n2 = b64_val(c2)?;
        let n3 = b64_val(c3)?;
        let n4 = b64_val(c4)?;

        let triple = (n1 << 18) | (n2 << 12) | (n3 << 6) | n4;

        buffer.push(((triple >> 16) & 0xFF) as u8);
        if c3 != '=' {
            buffer.push(((triple >> 8) & 0xFF) as u8);
        }
        if c4 != '=' {
            buffer.push((triple & 0xFF) as u8);
        }

        i += 4;
    }

    Ok(buffer)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decode_base64_basic() {
        // "SGVsbG8gV29ybGQ=" -> "Hello World"
        let decoded = decode_base64("SGVsbG8gV29ybGQ=").unwrap();
        assert_eq!(String::from_utf8(decoded).unwrap(), "Hello World");
    }

    #[test]
    fn test_decode_base64_data_uri() {
        let uri = "data:text/plain;base64,SGVsbG8=";
        let decoded = decode_base64(uri).unwrap();
        assert_eq!(String::from_utf8(decoded).unwrap(), "Hello");
    }
}
