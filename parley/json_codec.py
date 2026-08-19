"""The dependency-free JSON codec both backends embed.

One strict `Codec` runtime (accepted as the v0.5.5 cold-web-build product and
exercised by studies 044-047 at typed route boundaries) plus the per-record
and per-kind impl generator. The command target's `from json` / `as json` and
the web target's route bodies embed exactly this code, so the two boundaries
cannot drift. The Rust module keeps its historical name
`parley_web_json_runtime`; renaming it would churn generated output for no
behavioural gain.
"""

from __future__ import annotations

from . import ast_nodes as A
from .emit_rust import camel, rust_str_lit, rust_type, safe

JSON_RUNTIME = r'''
mod parley_web_json_runtime {
    use std::collections::BTreeMap;

    pub(crate) enum Value {
        Null,
        Bool(bool),
        Number(String),
        String(String),
        Array(Vec<Value>),
        Object(Vec<(String, Value)>),
    }

    pub(crate) trait Codec: Sized {
        fn decode(value: &Value) -> Result<Self, String>;
        fn encode(&self, output: &mut String) -> Result<(), String>;
    }

    pub(crate) fn decode<T: Codec>(text: &str) -> Result<T, String> {
        let value = Parser::new(text).parse()?;
        T::decode(&value)
    }

    pub(crate) fn encode<T: Codec>(value: &T) -> Result<String, String> {
        let mut output = String::new();
        value.encode(&mut output)?;
        Ok(output)
    }

    pub(crate) fn object(value: &Value) -> Result<&[(String, Value)], String> {
        match value {
            Value::Object(fields) => Ok(fields),
            _ => Err("expected JSON object".to_string()),
        }
    }

    pub(crate) fn string(value: &Value) -> Result<&str, String> {
        match value {
            Value::String(text) => Ok(text),
            _ => Err("expected JSON string".to_string()),
        }
    }

    pub(crate) fn write_member<T: Codec>(
        name: &str,
        value: &T,
        output: &mut String,
        first: &mut bool,
    ) -> Result<(), String> {
        if !*first { output.push(','); }
        *first = false;
        write_string(name, output);
        output.push(':');
        value.encode(output)
    }

    pub(crate) fn write_string(value: &str, output: &mut String) {
        use std::fmt::Write as _;
        output.push('"');
        for character in value.chars() {
            match character {
                '"' => output.push_str("\\\""),
                '\\' => output.push_str("\\\\"),
                '\u{08}' => output.push_str("\\b"),
                '\u{0c}' => output.push_str("\\f"),
                '\n' => output.push_str("\\n"),
                '\r' => output.push_str("\\r"),
                '\t' => output.push_str("\\t"),
                character if character <= '\u{1f}' => {
                    let _ = write!(output, "\\u{:04x}", character as u32);
                }
                character => output.push(character),
            }
        }
        output.push('"');
    }

    impl Codec for i64 {
        fn decode(value: &Value) -> Result<Self, String> {
            match value {
                Value::Number(number) => number.parse::<i64>()
                    .map_err(|_| "expected whole JSON number in i64 range".to_string()),
                _ => Err("expected JSON number".to_string()),
            }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push_str(&self.to_string());
            Ok(())
        }
    }

    impl Codec for f64 {
        fn decode(value: &Value) -> Result<Self, String> {
            let parsed = match value {
                Value::Number(number) => number.parse::<f64>()
                    .map_err(|_| "expected finite JSON number".to_string())?,
                _ => return Err("expected JSON number".to_string()),
            };
            if parsed.is_finite() { Ok(parsed) }
            else { Err("expected finite JSON number".to_string()) }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            if !self.is_finite() { return Err("cannot encode non-finite decimal".to_string()); }
            let rendered = self.to_string();
            output.push_str(&rendered);
            if !rendered.contains('.') && !rendered.contains('e') && !rendered.contains('E') {
                output.push_str(".0");
            }
            Ok(())
        }
    }

    impl Codec for bool {
        fn decode(value: &Value) -> Result<Self, String> {
            match value {
                Value::Bool(value) => Ok(*value),
                _ => Err("expected JSON boolean".to_string()),
            }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push_str(if *self { "true" } else { "false" });
            Ok(())
        }
    }

    impl Codec for String {
        fn decode(value: &Value) -> Result<Self, String> {
            string(value).map(str::to_string)
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            write_string(self, output);
            Ok(())
        }
    }

    impl<T: Codec> Codec for Option<T> {
        fn decode(value: &Value) -> Result<Self, String> {
            match value {
                Value::Null => Ok(None),
                value => T::decode(value).map(Some),
            }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            match self {
                Some(value) => value.encode(output),
                None => { output.push_str("null"); Ok(()) }
            }
        }
    }

    impl<T: Codec> Codec for Vec<T> {
        fn decode(value: &Value) -> Result<Self, String> {
            let values = match value {
                Value::Array(values) => values,
                _ => return Err("expected JSON array".to_string()),
            };
            values.iter().map(T::decode).collect()
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push('[');
            for (index, value) in self.iter().enumerate() {
                if index > 0 { output.push(','); }
                value.encode(output)?;
            }
            output.push(']');
            Ok(())
        }
    }

    impl<T: Codec> Codec for BTreeMap<String, T> {
        fn decode(value: &Value) -> Result<Self, String> {
            let mut output = BTreeMap::new();
            for (key, value) in object(value)? {
                output.insert(key.clone(), T::decode(value)?);
            }
            Ok(output)
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push('{');
            for (index, (key, value)) in self.iter().enumerate() {
                if index > 0 { output.push(','); }
                write_string(key, output);
                output.push(':');
                value.encode(output)?;
            }
            output.push('}');
            Ok(())
        }
    }

    struct Parser<'a> {
        text: &'a str,
        index: usize,
    }

    impl<'a> Parser<'a> {
        fn new(text: &'a str) -> Self { Self { text, index: 0 } }

        fn parse(mut self) -> Result<Value, String> {
            self.whitespace();
            let value = self.value(0)?;
            self.whitespace();
            if self.index != self.text.len() {
                return Err(format!("unexpected trailing JSON at byte {}", self.index));
            }
            Ok(value)
        }

        fn value(&mut self, depth: usize) -> Result<Value, String> {
            if depth > 128 { return Err("JSON nesting exceeds 128 levels".to_string()); }
            self.whitespace();
            match self.peek() {
                Some(b'n') => { self.literal("null")?; Ok(Value::Null) }
                Some(b't') => { self.literal("true")?; Ok(Value::Bool(true)) }
                Some(b'f') => { self.literal("false")?; Ok(Value::Bool(false)) }
                Some(b'"') => self.quoted().map(Value::String),
                Some(b'[') => self.array(depth + 1),
                Some(b'{') => self.object(depth + 1),
                Some(b'-' | b'0'..=b'9') => self.number().map(Value::Number),
                Some(_) => Err(format!("unexpected JSON value at byte {}", self.index)),
                None => Err("unexpected end of JSON".to_string()),
            }
        }

        fn array(&mut self, depth: usize) -> Result<Value, String> {
            self.index += 1;
            self.whitespace();
            let mut values = Vec::new();
            if self.take(b']') { return Ok(Value::Array(values)); }
            loop {
                values.push(self.value(depth)?);
                self.whitespace();
                if self.take(b']') { return Ok(Value::Array(values)); }
                if !self.take(b',') { return Err("expected comma or ] in JSON array".to_string()); }
                self.whitespace();
            }
        }

        fn object(&mut self, depth: usize) -> Result<Value, String> {
            self.index += 1;
            self.whitespace();
            let mut fields = Vec::new();
            if self.take(b'}') { return Ok(Value::Object(fields)); }
            loop {
                if self.peek() != Some(b'"') { return Err("expected string key in JSON object".to_string()); }
                let key = self.quoted()?;
                self.whitespace();
                if !self.take(b':') { return Err("expected colon after JSON object key".to_string()); }
                fields.push((key, self.value(depth)?));
                self.whitespace();
                if self.take(b'}') { return Ok(Value::Object(fields)); }
                if !self.take(b',') { return Err("expected comma or } in JSON object".to_string()); }
                self.whitespace();
            }
        }

        fn number(&mut self) -> Result<String, String> {
            let start = self.index;
            self.take(b'-');
            match self.peek() {
                Some(b'0') => {
                    self.index += 1;
                    if matches!(self.peek(), Some(b'0'..=b'9')) {
                        return Err("JSON number has a leading zero".to_string());
                    }
                }
                Some(b'1'..=b'9') => {
                    self.index += 1;
                    while matches!(self.peek(), Some(b'0'..=b'9')) { self.index += 1; }
                }
                _ => return Err("invalid JSON number".to_string()),
            }
            if self.take(b'.') {
                let fraction = self.index;
                while matches!(self.peek(), Some(b'0'..=b'9')) { self.index += 1; }
                if self.index == fraction { return Err("JSON fraction needs digits".to_string()); }
            }
            if matches!(self.peek(), Some(b'e' | b'E')) {
                self.index += 1;
                if matches!(self.peek(), Some(b'+' | b'-')) { self.index += 1; }
                let exponent = self.index;
                while matches!(self.peek(), Some(b'0'..=b'9')) { self.index += 1; }
                if self.index == exponent { return Err("JSON exponent needs digits".to_string()); }
            }
            Ok(self.text[start..self.index].to_string())
        }

        fn quoted(&mut self) -> Result<String, String> {
            self.index += 1;
            let mut output = String::new();
            loop {
                let byte = self.peek().ok_or_else(|| "unterminated JSON string".to_string())?;
                match byte {
                    b'"' => { self.index += 1; return Ok(output); }
                    b'\\' => {
                        self.index += 1;
                        let escape = self.peek().ok_or_else(|| "unterminated JSON escape".to_string())?;
                        self.index += 1;
                        match escape {
                            b'"' => output.push('"'), b'\\' => output.push('\\'), b'/' => output.push('/'),
                            b'b' => output.push('\u{08}'), b'f' => output.push('\u{0c}'),
                            b'n' => output.push('\n'), b'r' => output.push('\r'), b't' => output.push('\t'),
                            b'u' => output.push(self.unicode_escape()?),
                            _ => return Err("invalid JSON string escape".to_string()),
                        }
                    }
                    0..=31 => return Err("unescaped control byte in JSON string".to_string()),
                    _ => {
                        let character = self.text[self.index..].chars().next()
                            .ok_or_else(|| "invalid UTF-8 in JSON string".to_string())?;
                        output.push(character);
                        self.index += character.len_utf8();
                    }
                }
            }
        }

        fn unicode_escape(&mut self) -> Result<char, String> {
            let first = self.hex_quad()?;
            let scalar = if (0xd800..=0xdbff).contains(&first) {
                if !self.take(b'\\') || !self.take(b'u') {
                    return Err("high surrogate must be followed by a low surrogate".to_string());
                }
                let second = self.hex_quad()?;
                if !(0xdc00..=0xdfff).contains(&second) {
                    return Err("invalid low surrogate in JSON string".to_string());
                }
                0x10000 + ((first - 0xd800) << 10) + (second - 0xdc00)
            } else {
                if (0xdc00..=0xdfff).contains(&first) {
                    return Err("unexpected low surrogate in JSON string".to_string());
                }
                first
            };
            char::from_u32(scalar).ok_or_else(|| "invalid Unicode scalar in JSON string".to_string())
        }

        fn hex_quad(&mut self) -> Result<u32, String> {
            let mut value = 0u32;
            for _ in 0..4 {
                let byte = self.peek().ok_or_else(|| "short Unicode escape".to_string())?;
                self.index += 1;
                value = value * 16 + match byte {
                    b'0'..=b'9' => (byte - b'0') as u32,
                    b'a'..=b'f' => (byte - b'a' + 10) as u32,
                    b'A'..=b'F' => (byte - b'A' + 10) as u32,
                    _ => return Err("invalid hex digit in Unicode escape".to_string()),
                };
            }
            Ok(value)
        }

        fn literal(&mut self, expected: &str) -> Result<(), String> {
            if self.text[self.index..].starts_with(expected) {
                self.index += expected.len();
                Ok(())
            } else {
                Err(format!("invalid JSON literal at byte {}", self.index))
            }
        }

        fn whitespace(&mut self) {
            while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) { self.index += 1; }
        }

        fn peek(&self) -> Option<u8> { self.text.as_bytes().get(self.index).copied() }

        fn take(&mut self, wanted: u8) -> bool {
            if self.peek() == Some(wanted) { self.index += 1; true } else { false }
        }
    }
}
'''


def direct_json_impls(program: A.Program) -> str:
    """Emit strict codecs for typed routes without third-party Rust crates."""
    chunks: list[str] = []
    runtime = "parley_web_json_runtime"
    for record in program.records:
        type_name = camel(record.name)
        declarations = "\n".join(
            f"        let mut parley_field_{safe(field)}: "
            f"Option<{rust_type(field_type)}> = None;"
            for field, field_type in record.fields
        )
        match_arms = "\n".join(
            f'''                "{rust_str_lit(field)}" => {{
                    if parley_field_{safe(field)}.is_some() {{
                        return Err("duplicate field {rust_str_lit(field)}".to_string());
                    }}
                    parley_field_{safe(field)} = Some(<{rust_type(field_type)} as {runtime}::Codec>::decode(parley_value)?);
                }}'''
            for field, field_type in record.fields
        )
        required_fields: list[str] = []
        for field, field_type in record.fields:
            variable = f"parley_field_{safe(field)}"
            if isinstance(field_type, A.TMaybe):
                required_fields.append(
                    f"        let {variable} = {variable}.unwrap_or(None);"
                )
            else:
                required_fields.append(
                    f'''        let {variable} = {variable}.ok_or_else(||
            "missing field {rust_str_lit(field)}".to_string())?;'''
                )
        initializers = ", ".join(
            f"{safe(field)}: parley_field_{safe(field)}"
            for field, _field_type in record.fields
        )
        encode_fields = "\n".join(
            f'        {runtime}::write_member("{rust_str_lit(field)}", '
            f'&self.{safe(field)}, output, &mut first)?;'
            for field, _field_type in record.fields
        )
        chunks.append(f'''
impl {runtime}::Codec for {type_name} {{
    fn decode(value: &{runtime}::Value) -> Result<Self, String> {{
        let parley_fields = {runtime}::object(value)?;
{declarations}
        for (parley_key, parley_value) in parley_fields {{
            match parley_key.as_str() {{
{match_arms}
                _ => return Err(format!("unknown field {{}}", parley_key)),
            }}
        }}
{chr(10).join(required_fields)}
        Ok({type_name} {{ {initializers} }})
    }}

    fn encode(&self, output: &mut String) -> Result<(), String> {{
        output.push('{{');
        let mut first = true;
{encode_fields}
        output.push('}}');
        Ok(())
    }}
}}
'''.strip())

    for enum in program.enums:
        type_name = camel(enum.name)
        decode_arms = "\n".join(
            f'            "{rust_str_lit(variant)}" => Ok({type_name}::{camel(variant)}),'
            for variant in enum.variants
        )
        encode_arms = "\n".join(
            f'            {type_name}::{camel(variant)} => "{rust_str_lit(variant)}",'
            for variant in enum.variants
        )
        expected = ", ".join(enum.variants)
        chunks.append(f'''
impl {runtime}::Codec for {type_name} {{
    fn decode(value: &{runtime}::Value) -> Result<Self, String> {{
        match {runtime}::string(value)? {{
{decode_arms}
            other => Err(format!("unknown variant {{}}; expected one of {rust_str_lit(expected)}", other)),
        }}
    }}

    fn encode(&self, output: &mut String) -> Result<(), String> {{
        {runtime}::write_string(match self {{
{encode_arms}
        }}, output);
        Ok(())
    }}
}}
'''.strip())
    return "\n\n".join(chunks)
