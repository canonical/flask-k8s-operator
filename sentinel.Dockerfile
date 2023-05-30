FROM ubuntu:latest

RUN cp /dev/null /null

FROM scratch

COPY --from=0 /null /null
