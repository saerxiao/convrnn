CUDA_VISIBLE_DEVICES=5 python train.py --dataroot /data/mri/data/color_fa_sliced/t123_colorfa --name t1_colorfa_L1_unet128_T3_3d --which_model_netG unet_128_3d --which_model_netD basic_3d --which_direction AtoB --dataset_mode aligned --no_lsgan --norm batch --pool_size 0 --content_only --T 3 --predict_idx_type middle --output_nc 3 --with_logit_loss --norm batch_3d --conv_type 3d --loadSize 128 --fineSize 128 --data_suffix png --valid_folder val --use_L1 --input_nc 1 --input_channels 0 --validate_freq 1000 --niter 5 --niter_decay 5
