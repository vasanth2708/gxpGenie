FROM public.ecr.aws/sam/build-python3.12:1.125.0-20240926224229

RUN dnf install -y gcc python3-devel && dnf clean all

WORKDIR /var/task

COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt --no-cache-dir

COPY ./rag .

CMD ["main.handler"]
