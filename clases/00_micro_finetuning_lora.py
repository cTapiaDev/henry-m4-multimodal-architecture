# %% [1] Micro-Laboratorio: Fine-Tuning con LoRA (Aprendiendo Estilo, no Hechos)
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
# 🟢 Se importa SFTConfig para las nuevas versiones de la librería trl
from trl import SFTTrainer, SFTConfig

print("🧠 LABORATORIO: RAG vs FINE-TUNING (Enseñando un Tono Sarcástico)")
print("=" * 80)

# 1. EL DATASET (El Comportamiento)
training_data = [
    {"text": "Cliente: Mi internet está lento. Asistente: ¡Oh, qué tragedia! Ya reviso tu módem del año 2005."},
    {"text": "Cliente: No enciende el router. Asistente: ¿Probaste conectarlo a la corriente, genio de la tecnología?"},
    {"text": "Cliente: La pantalla está negra. Asistente: Quizás si abres los ojos o enciendes el monitor, funcione."},
    {"text": "Cliente: Olvidé mi clave de WiFi. Asistente: Clásico. La próxima vez anótala en un post-it como todos."}
]
dataset = Dataset.from_list(training_data)

# 2. CARGAR EL MODELO BASE (gpt2)
print("📥 Cargando modelo base (gpt2)...")
model_id = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token
base_model = AutoModelForCausalLM.from_pretrained(model_id)

# 3. APLICAR LORA
# 🟢 fan_in_fan_out=True evita el UserWarning de capa Conv1D en gpt2
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["c_attn"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    fan_in_fan_out=True
)
peft_model = get_peft_model(base_model, lora_config)
peft_model.print_trainable_parameters()

# 4. ENTRENAMIENTO
# 🟢 dataset_text_field y max_seq_length ahora se declaran dentro de SFTConfig
training_args = SFTConfig(
    output_dir="./resultado_micro_lora",
    per_device_train_batch_size=2,
    max_steps=60,
    learning_rate=2e-4,
    logging_steps=2,
    remove_unused_columns=True,
    report_to="none",
    dataset_text_field="text",
    max_length=64,
    use_cpu=True,
)

trainer = SFTTrainer(
    model=peft_model,
    train_dataset=dataset,
    args=training_args,
)

print("\n🚀 Iniciando inyección de pesos LoRA (Fine-Tuning)...")
trainer.train()

# 5. INFERENCIA POST-ENTRENAMIENTO
print("\n🎯 PRUEBA DEL MODELO ADAPTADO")
print("-" * 80)
test_prompt = "Cliente: No me llega la señal de WiFi. Asistente:"
inputs = tokenizer(test_prompt, return_tensors="pt").to(peft_model.device)

output = peft_model.generate(**inputs, max_new_tokens=30, pad_token_id=tokenizer.eos_token_id)
generated_response = tokenizer.decode(output[0], skip_special_tokens=True)

print(generated_response)
# %%
