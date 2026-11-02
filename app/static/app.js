"use strict";

const form = document.querySelector("#analysis-form");
const content = document.querySelector("#content");
const category = document.querySelector("#category");
const button = document.querySelector("#submit-button");
const status = document.querySelector("#status");
const result = document.querySelector("#result");
const count = document.querySelector("#char-count");

content.addEventListener("input", () => {
  count.textContent = content.value.length.toLocaleString("pt-PT") + " / 20 000";
});

function addTextItem(list, text, className) {
  const item = document.createElement("li");
  if (className) item.className = className;
  item.textContent = String(text ?? "");
  list.append(item);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!content.value.trim()) {
    status.textContent = "Escreve uma questão antes de enviar.";
    status.className = "status error";
    return;
  }

  button.disabled = true;
  status.className = "status";
  status.textContent = "A analisar…";
  result.hidden = true;

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ content: content.value, category: category.value }),
      cache: "no-store"
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(response.status === 422
        ? "O pedido não passou a validação. Verifica o texto e a categoria."
        : response.status === 503
          ? "O fornecedor de IA está temporariamente indisponível."
          : "Não foi possível concluir a análise.");
    }

    const guidance = document.querySelector("#guidance");
    const sources = document.querySelector("#sources");
    guidance.replaceChildren();
    sources.replaceChildren();
    (data.guidance || []).forEach((entry) => addTextItem(guidance, entry));
    (data.sources || []).forEach((source) => {
      addTextItem(sources, source.title + " — " + source.path + ": " + source.excerpt);
    });
    document.querySelector("#provider").textContent =
      "Fornecedor: " + data.provider + " · Estado: " + data.status;
    result.hidden = false;
    status.textContent = "Análise concluída.";
  } catch (error) {
    status.textContent = error instanceof TypeError
      ? "Não foi possível contactar a API. Tenta novamente mais tarde."
      : error.message;
    status.className = "status error";
  } finally {
    button.disabled = false;
  }
});
