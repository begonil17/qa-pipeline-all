from evaluation.hf_client import HFClient

client = HFClient()

answer = client.generate("Türkiye'nin başkenti neresidir?")

print("Final answer:", repr(answer))