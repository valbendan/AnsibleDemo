
format:
	poetry run black *.py


extract-ansible-doc:
	poetry run python gen_ansible_doc.py docs
