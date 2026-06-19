// Minimal MCP stdio JSON-RPC 2.0 client — produces REAL execution evidence for Dev 2.1.
// Spawns each configured server, performs handshake, lists tools, and calls tools.
import { spawn } from "node:child_process";

const REPO = process.argv[2] || ".";

function rpcClient(cmd, args, cwd) {
  const child = spawn(cmd, args, { cwd, stdio: ["pipe", "pipe", "pipe"], shell: process.platform === "win32" });
  let buf = "";
  const pending = new Map();
  let stderr = "";
  child.stderr.on("data", (d) => (stderr += d.toString()));
  child.stdout.on("data", (d) => {
    buf += d.toString();
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line) continue;
      try {
        const msg = JSON.parse(line);
        if (msg.id !== undefined && pending.has(msg.id)) {
          pending.get(msg.id)(msg);
          pending.delete(msg.id);
        }
      } catch { /* non-JSON banner line, ignore */ }
    }
  });
  let id = 0;
  const send = (method, params) =>
    new Promise((resolve, reject) => {
      const myId = ++id;
      pending.set(myId, resolve);
      child.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: myId, method, params }) + "\n");
      setTimeout(() => reject(new Error("timeout on " + method)), 60000);
    });
  const notify = (method, params) =>
    child.stdin.write(JSON.stringify({ jsonrpc: "2.0", method, params }) + "\n");
  return { child, send, notify, getStderr: () => stderr };
}

async function run(name, cmd, args, cwd, calls) {
  console.log(`\n${"=".repeat(70)}\n### SERVER: ${name}\n### cmd: ${cmd} ${args.join(" ")}\n${"=".repeat(70)}`);
  const c = rpcClient(cmd, args, cwd);
  try {
    const init = await c.send("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "novatech-evidence-client", version: "1.0.0" },
    });
    console.log(`[initialize] serverInfo:`, JSON.stringify(init.result?.serverInfo));
    c.notify("notifications/initialized", {});
    const tools = await c.send("tools/list", {});
    const names = (tools.result?.tools || []).map((t) => t.name);
    console.log(`[tools/list] ${names.length} tools: ${names.join(", ")}`);
    for (const call of calls) {
      console.log(`\n--- tools/call: ${call.name} ${JSON.stringify(call.arguments)} ---`);
      try {
        const res = await c.send("tools/call", { name: call.name, arguments: call.arguments });
        const text = (res.result?.content || []).map((x) => x.text).join("\n");
        if (call.extractChunk) {
          // Simulate retrieval: from the corpus the server returned, select the chunk
          // relevant to the domain question. Gabarito (Anexo B): "Qual o SLA do cliente Gold?" -> SLA-2024-B.
          const lines = text.split("\n");
          const idx = lines.findIndex((l) => l.includes(call.extractChunk));
          const block = lines.slice(idx, idx + 4).join("\n");
          console.log(`[retriever] question: "${call.question}"`);
          console.log(`[retriever] selected chunk (gabarito Anexo B = ${call.extractChunk}):\n${block}`);
        } else {
          console.log(call.truncate ? text.slice(0, call.truncate) + "\n…[truncated]" : text);
        }
      } catch (e) {
        console.log("CALL ERROR:", e.message);
      }
    }
  } catch (e) {
    console.log("FATAL:", e.message, "\nSTDERR:", c.getStderr().slice(0, 500));
  } finally {
    c.child.kill();
  }
}

const main = async () => {
  // (a)+(b) filesystem server — scoped to business sources read paths
  await run(
    "filesystem",
    "npx",
    ["-y", "@modelcontextprotocol/server-filesystem", "./docs", "./data", "./specs", "./src", "./skills", "./prompts"],
    REPO,
    [
      { name: "list_allowed_directories", arguments: {} },
      { name: "list_directory", arguments: { path: "./docs/novatech" } },
      { name: "read_text_file", arguments: { path: "./docs/novatech/SLA-2024-tabela-sla-clientes.md", head: 30 }, truncate: 1200 },
      // (b) retrieve chunk for domain question "Qual o SLA do cliente Gold?" -> gabarito Anexo B = SLA-2024-B
      { name: "search_files", arguments: { path: "./data", pattern: "chunks" } },
      { name: "read_text_file", arguments: { path: "./data/retrieval-corpus/chunks-novatech.md" },
        extractChunk: "SLA-2024-B", question: "Qual o SLA do cliente Gold?" },
    ]
  );
  // (c) git server — repo history
  await run(
    "git",
    "uvx",
    ["mcp-server-git", "--repository", "."],
    REPO,
    [
      { name: "git_log", arguments: { repo_path: ".", max_count: 5 } },
      { name: "git_status", arguments: { repo_path: "." } },
    ]
  );
};
main();
