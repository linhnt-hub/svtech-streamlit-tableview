FROM python:3.10.12-slim

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends libc6-dev make dpkg-dev git openssh-client \
    && apt-get clean all \
    && rm -rf /var/cache/apt/archives /var/lib/apt/lists/*
ARG git_token
ARG user_email
ARG user_name
ENV DB_DIR="/SVTECH-Junos-Automation/Python-Development/streamlit_apps/optic_data"
#########git clone#########
# # Clone the conf files into the docker container
RUN /usr/bin/git clone -n --depth=1 --filter=tree:0 --no-checkout --branch Developer https://$git_token@github.com/moophat/SVTECH-Junos-Automation.git
RUN cd SVTECH-Junos-Automation && git sparse-checkout set --no-cone module_utils Junos_tableview Python-Development/streamlit_apps && git checkout
COPY streamlit_pyez_utilities.py /SVTECH-Junos-Automation/Python-Development/streamlit_apps/streamlit_pyez_utilities.py
# ########done git clone#########
RUN git config --global user.email "${user_email}" \
    && git config --global user.name "${user_name}"

WORKDIR /SVTECH-Junos-Automation/Python-Development/streamlit_apps
COPY default_variable.yml /root/default_variable.yml 
ENV VAR_PATH="/root/default_variable.yml"
COPY entrypoint.sh /root/entrypoint.sh
RUN ["chmod", "+x", "/root/entrypoint.sh"]

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --no-cache-dir
COPY ./yamllint_conf/default.yaml /usr/local/lib/python3.10/site-packages/yamllint/conf
COPY ./yamllint_conf/relaxed.yaml /usr/local/lib/python3.10/site-packages/yamllint/conf
EXPOSE 8501
ENTRYPOINT [ "/root/entrypoint.sh" ]