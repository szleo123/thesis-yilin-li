from pathlib import Path
from torch.utils.data import Dataset
from tokenizers import ByteLevelBPETokenizer, CharBPETokenizer, Tokenizer
from tokenizers.models import BPE, Unigram
from tokenizers.trainers import BpeTrainer, UnigramTrainer
from os.path import join

paths = [str(x) for x in Path("./Data/").glob("*.txt")]
VOCAB_SIZE = 52_000
model_dir = './BPE_spaced'


def create_tokenizer():
    tokenizer = ByteLevelBPETokenizer()
    #tokenizer = CharBPETokenizer()
    #tokenizer = Tokenizer(Unigram())
    tokenizer.train(files=paths,
                    vocab_size=VOCAB_SIZE,
                    min_frequency=2,
                    special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>", "</w>"])
    tokenizer.save_model(model_dir)


def validate_tokenizer():
    # Encoding(num_tokens=7, ...)
    # tokens: ['<s>', 'Mi', 'Ġestas', 'ĠJuli', 'en', '.', '</s>']
    from tokenizers.implementations import ByteLevelBPETokenizer
    from tokenizers.processors import BertProcessing
    tokenizer = ByteLevelBPETokenizer(
        join(model_dir, "vocab.json"),
        join(model_dir, "merges.txt"),
    )
    tokenizer._tokenizer.post_processor = BertProcessing(
        ("</s>", tokenizer.token_to_id("</s>")),
        ("<s>", tokenizer.token_to_id("<s>")),
    )
    tokenizer.enable_truncation(max_length=512)


def init_trainer():
    from transformers import GPT2Model, GPT2Config, GPT2LMHeadModel
    from transformers import GPT2Tokenizer
    config = GPT2Config(
        vocab_size=VOCAB_SIZE,
        #max_position_embeddings=514,
        #num_attention_heads=12,
        #num_hidden_layers=6,
        #type_vocab_size=1,
    )
    tokenizer = GPT2Tokenizer.from_pretrained(model_dir, max_len=512)
    model = GPT2LMHeadModel(config=config)
    print('Num parameters: {}'.format(model.num_parameters()))
    from transformers import TextDataset
    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path="./Data/train.en.txt",
        block_size=128,
    )
    print(dataset[0])
    from transformers import DataCollatorForLanguageModeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False
    )
    from transformers import Trainer, TrainingArguments
    training_args = TrainingArguments(
        output_dir=model_dir,
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_gpu_train_batch_size=1,
        save_steps=10_000,
        save_total_limit=2,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=dataset,
        #prediction_loss_only=True,
    )
    return trainer


def start_training(trainer):
    trainer.train()
    trainer.save_model(model_dir)



def pipeline():
    create_tokenizer()
    trainer = init_trainer()
    start_training(trainer)

pipeline()