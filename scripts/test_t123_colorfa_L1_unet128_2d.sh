CUDA_VISIBLE_DEVICES=1 python test.py --dataroot /data/mri/data/color_fa_sliced/t123_colorfa --name t123_colorfa_L1_unet128_2d --which_model_netG unet_128 --which_model_netD basic --which_direction AtoB --dataset_mode aligned --norm batch --content_only --T 1 --predict_idx_type middle --output_nc 3 --norm batch --loadSize 128 --fineSize 128 --data_suffix png --valid_folder val --conv_type 2d --display_type single --which_epoch lowest_val