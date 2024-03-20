FROM ubuntu:22.04
ARG git_token
ENV DB_DIR="/SVTECH-Junos-Automation/Python-Development/streamlit_apps/optic_data"
# #need to change to git clone & copy neccessary file to target location
# ########git clone#########
RUN apt-get update -y &&  apt-get -y install && apt-get install -y git && apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev && wget https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz && tar -xf Python-3.9.5.tgz && cd Python-3.9.5 && ./configure --enable-optimizations && make -j 12 && make altinstall && apt-get -y install python3-pip
# && apt-get install -y software-properties-common && add-apt-repository -y ppa:deadsnakes/ppa && apt-get -y install python3.9 && apt-get -y install python3-pip
# # Clone the conf files into the docker container
RUN git clone -n --depth=1 --filter=tree:0 --no-checkout --branch Developer\
  https://${git_token}@github.com/moophat/SVTECH-Junos-Automation.git
RUN cd SVTECH-Junos-Automation && git sparse-checkout set --no-cone module_utils Junos_tableview Python-Development/streamlit_apps  && git checkout
# ########done git clone#########
# ########start install##########
WORKDIR /SVTECH-Junos-Automation/Python-Development/streamlit_apps
COPY entrypoint.sh /root/entrypoint.sh
RUN ["chmod", "+x", "/root/entrypoint.sh"]
# Create default db_dir
# RUN mkdir -p ${DB_DIR}
RUN pip3 install -r requirements.txt
EXPOSE 8501
ENTRYPOINT [ "/root/entrypoint.sh" ]
# ENTRYPOINT ["streamlit", "run", "streamlit_mainpage.py", "--server.port=8501", "--server.address=0.0.0.0"]